-- This file about generating the navboxes from the game file instead of adding objects manually in them.  
-- Write doc on the wiki with https://wiki.desyncedgame.com/index.php?title=Module:Navboxes/doc&action=edit

local p = {}
local m = {} -- Use for internal function. You can use this one for debugging without exposing functions, return this instead of p

---@type any
---@diagnostic disable-next-line: lowercase-global
mw = mw

local cargo = mw.ext.cargo

local function stripWhitespace(str)
    return str:match("^%s*(.-)%s*$")
end

local _cache = {
  base = {},
  extras = {},
  bugs = nil
}

local _expandCache = {}

local function expandCached(frame, title, args)
  local key = title .. '|' .. (args.name or '')

  if _expandCache[key] then
    return _expandCache[key]
  end

  local result = stripWhitespace(frame:expandTemplate{
    title = title,
    args = args
  })

  _expandCache[key] = result
  return result
end

local CATEGORY_FILTER_TABLE = "categoryfilter"
local USER_NAV_CATEGORIES_TABLE = "userNavCategories"

---@class TypeData
---@comment Contains categoryfilter selectors for given type
---@field cargo_table string
---@field extra_fields string|nil Fields to query, beside name
---@field tab string
---@field filterField string
---@field recipeType string|nil
---@field orderBy string|nil

---@alias NavboxType "BOT" | "BUILDING" | "COMPONENT" | "ITEM"

-- Possible types to create a navbox with
-- THe filter fields & recipe types are about listing & filtering like the game does
---@type table<NavboxType, TypeData>
local TYPES = {
  BOT = {
    cargo_table = "entity",
    extra_fields = "race, slotType",
    tab = "frame",
    filterField = "size",
    recipeType = "Production"
  },
  BUILDING = {
    cargo_table = "entity",
    tab = "frame",
    filterField = "size",
    recipeType = "Construction",
  },
  COMPONENT = {
    cargo_table = "component",
    tab = "item",
    filterField = "attachmentSize",
  },
  ITEM = {
    cargo_table = "item",
    extra_fields = "type, race",
    tab = "item",
    filterField = "tag",
    orderBy = "type, race"
  }
}

---@class CategoryData
---@field ordering number?
---@field names string[]

---@param categories table<string, CategoryData>
---@return nil
m.removeEmptyCategories = function(categories)
 for k, v in pairs(categories) do
    if #(v.names) == 0 then
      categories[k] = nil
    end
  end
end

---@param categories table<string, CategoryData>
---@param cat_name string
---@param name string
---@param ordering number
---@return nil
m.createOrAppendToCategory = function(categories, cat_name, name, ordering)
   -- If the category doesn't exist, create it
    if not categories[cat_name] then
        categories[cat_name] = {
            ordering = ordering,
            names = {}
        }
    end

    -- Append the new name
    table.insert(categories[cat_name].names, name)
end


---Custom sorting for bots here
---@param type NavboxType
---@param categories table<string, CategoryData>
---@param game_cat_name string
---@param ordering number
---@param row table
---@return nil
m.sortInCategory = function(type, categories, game_cat_name, ordering, row)
  if type == "BOT" then
    if row.slotType ~= nil and mw.ustring.upper(row.slotType) == "DRONE" then
      m.createOrAppendToCategory(categories, "Drone", row.name, ordering)
    elseif row.slotType ~= nil and mw.ustring.upper(row.slotType) == "SATELLITE" then -- Doesn't actually get passed to this function atm
      m.createOrAppendToCategory(categories, "Satellite", row.name, ordering)
    elseif row.race ~= nil then
      m.createOrAppendToCategory(categories, row.race, row.name, ordering)
    else -- fallback
      m.createOrAppendToCategory(categories, "Other", row.name, ordering)
    end
  else
    m.createOrAppendToCategory(categories, game_cat_name, row.name, ordering)
  end
end

---@param categories table<string, CategoryData>
---@return nil
m.addBugsBots = function(categories)
  if _cache.bugs then
    for _, row in ipairs(_cache.bugs) do
      m.createOrAppendToCategory(categories, "Bugs", row.name, 999)
    end
    return
  end

  local typeData = TYPES["BOT"]
  local query_objects = cargo.query(
    typeData.cargo_table,
    'name',
    {
      where = 'size = "Unit" AND race = "Virus"'
    }
  )

  _cache.bugs = query_objects

  for _, row in ipairs(query_objects) do
    m.createOrAppendToCategory(categories, "Bugs", row.name, 999)
  end
end

---@param type NavboxType
---@return table<string, CategoryData>
m.queryBaseCategories = function (type)
  if _cache.base[type] then
    return _cache.base[type]
  end

  local typeData = TYPES[type]

  -- STEP 1: get category metadata
  local categoriesMeta = cargo.query(
    CATEGORY_FILTER_TABLE .. "=cat",
    'name, filterVal, ordering',
    {
      where = string.format('tab="%s" AND filterField="%s"', typeData.tab, typeData.filterField),
      groupBy = 'cat.filterVal'
    }
  )

  -- build lookup table
  local filterToCategory = {}
  local categories = {}

  for _, cat in ipairs(categoriesMeta) do
    filterToCategory[cat.filterVal] = {
      name = cat.name,
      ordering = tonumber(cat.ordering) or 0
    }
  end

  -- STEP 2: single bulk object query
  local fields = 'name, unlockable,' .. typeData.filterField
  if typeData.extra_fields then
    fields = fields .. ',' .. typeData.extra_fields
  end

  local wherePart = 'unlockable = TRUE'
  if typeData.recipeType then
    wherePart = wherePart .. string.format(' AND recipeType="%s"', typeData.recipeType)
  end

  local allObjects = cargo.query(
    typeData.cargo_table,
    fields,
    {
      where = wherePart,
      orderBy = typeData.orderBy
    }
  )

  -- STEP 3: assign objects to categories in Lua
  for _, row in ipairs(allObjects) do
    local filterVal = row[typeData.filterField]
    local meta = filterToCategory[filterVal]

    if meta then
      m.sortInCategory(type, categories, meta.name, meta.ordering, row)
    end
  end

  -- BOT special handling
  if type == "BOT" then
    m.addBugsBots(categories)
  end

  _cache.base[type] = categories
  return categories
end

---@param type NavboxType
---@return table<string, CategoryData>
m.queryUserExtrasCategories = function(type)
  if _cache.extras[type] then
    return _cache.extras[type]
  end

  local userCategoriesRows = cargo.query(
    USER_NAV_CATEGORIES_TABLE,
    'category=catName, pagename',
    {
      where = string.format('UPPER(type) = "%s"', type)
    }
  )

  local categories = {}

  for _, row in ipairs(userCategoriesRows) do
    local catName = row.catName
    if not categories[catName] then
      categories[catName] = { ordering = 999, names = {} }
    end
    table.insert(categories[catName].names, row.pagename)
  end

  _cache.extras[type] = categories
  return categories
end

-- Names in extra have priority.
-- Does mutate base
---@param base table<string, CategoryData>
---@param extra table<string, CategoryData>
---@return table<string, CategoryData>
m.mergeCategories = function (base, extra)
  -- Step 1: Remove from base any name also found in extra
  for _, extraCat in pairs(extra) do
    for _, name in ipairs(extraCat.names) do
      for _, baseCat in pairs(base) do
        for i = #baseCat.names, 1, -1 do -- reverse loop to allow deletion while looping
          if baseCat.names[i] == name then
            table.remove(baseCat.names, i)
          end
        end
      end
    end
  end

  -- Step 2: Merge extra into base
  for catName, extraCat in pairs(extra) do
    if not base[catName] then
      base[catName] = extraCat
    else
      local target = base[catName].names
      for _, name in ipairs(extraCat.names) do
        table.insert(target, name)
      end
    end
  end

  return base
end

---@class SortedCategoryEntry
---@field name string
---@field data CategoryData

---@param categories table<string, CategoryData>
---@return SortedCategoryEntry[]
m.sortCategories = function(categories)
  -- Convert map to array
  local arr = {}
  for name, data in pairs(categories) do
    table.insert(arr, { name = name, data = data })
  end

  -- Sort by ordering (ascending)
  table.sort(arr, function(a, b)
    return (a.data.ordering) < (b.data.ordering)
  end)

  return arr
end

--- Build a navbox
-- @param {table} frame current frame
-- @param {string} frame.args.title Navtable title
-- @param {string} frame.args.type from types above here, like Building or Item (any case)
---@param tableTitle string Navtable title
---@param rawType string from types above here, like Building or Item (any case)
---@return string
m.createNavBox = function(tableTitle, rawType)
  ---@type NavboxType
  local type = mw.ustring.upper(rawType or "")
  local typeData = TYPES[type]
  if not typeData then
    return string.format("Navbox error: Unknown type: '%s'", type)
  end

  local frame = mw.getCurrentFrame()
  
  local baseCategories = m.queryBaseCategories(type)

  local extraCategories = m.queryUserExtrasCategories(type)

  local categories = m.mergeCategories(baseCategories, extraCategories)
  -- mw.logObject(categories) 
  m.removeEmptyCategories(categories)

  local sortedCategories = m.sortCategories(categories)

  local rowsHtml = ""
  for _, cat in ipairs(sortedCategories) do
    local objects = "" -- list of objects to insert in a row
    for _, name in ipairs(cat.data.names) do
      objects = objects .. expandCached(frame, "NavboxIconLinkNamed", { name = name })
    end
    -- Returns a table row [ category | objects ]
    rowsHtml = rowsHtml .. stripWhitespace(frame:expandTemplate {
      title = "NavTableCategory",
      args = {
        tableTitle = tableTitle,
        catName = cat.name,
        objects = objects
      }
    })
  end

  -- Final table
  return stripWhitespace(frame:expandTemplate {
    title = "NavTable",
    args = {
      title = tableTitle,
      rows = rowsHtml
    }
  })
end

--- Build a navbox
-- @param {table} frame current frame
-- @param {string} frame.args.title Navtable title
-- @param {string} frame.args.type from types above here, like Building or Item (any case)
---@return string
p.create = function(frame)
  local title = frame.args.title
  local rawType = frame.args.type
  if not title then
    return "(Navbox error: No title provided)"
  end
  if not rawType then
    return "(Navbox error: No type provided)"
  end
  return m.createNavBox(title, rawType)
end

return p



--[[
Debugging:

local frame = { args = { title = "Buildings", type = "Building" } }
local frame = { args = { title = "Bots", type = "BOT" } }
(enter)
= p.create(frame)
(enter)

Return m instead of p if you want to debug the non exposed functions

Resources:
General cargo: https://www.mediawiki.org/wiki/Extension:Cargo/Querying_data
Cargo querying from LUA: https://www.mediawiki.org/wiki/Extension:Cargo/Other_features#Lua_support
https://www.mediawiki.org/wiki/Extension:Scribunto/Lua_reference_manual

--]]
