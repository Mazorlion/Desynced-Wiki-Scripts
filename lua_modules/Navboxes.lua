-- Doc in the wiki doc page

local p = {}
local nav = {} -- you can use this one for debugging without exposing functions, return this instead of p

---@type any
---@diagnostic disable-next-line: lowercase-global
mw = mw

local cargo = mw.ext.cargo

local CATEGORY_FILTER_TABLE = "categoryfilter"
local USER_NAV_CATEGORIES_TABLE = "userNavCategories"
local function stripWhitespace(str)
    return str:match("^%s*(.-)%s*$")
end

---@class TypeData
---@comment Contains categoryfilter selectors for given type
---@field cargo_table string
---@field tab string
---@field filterField string
---@field recipeType string|nil

---@alias NavboxType "UNIT" | "BUILDING" | "COMPONENT" | "ITEM"

-- Possible types to create a navbox with
---@type table<NavboxType, TypeData>
local TYPES = {
  UNIT = {
    cargo_table = "entity",
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
    recipeType = nil --unused
  },
  ITEM = {
    cargo_table = "item",
    tab = "item",
    filterField = "tag",
    recipeType = nil --unused
  }
}

---@class CategoryData
---@field ordering number?
---@field names string[]

---@param categories table<string, CategoryData>
---@return nil
nav.removeEmptyCategories = function(categories)
 for k, v in pairs(categories) do
    if #(v.names) == 0 then
      categories[k] = nil
    end
  end
end

---@param typeData TypeData
---@return table<string, CategoryData>
nav.queryBaseCategories = function (typeData)
  local categoriesMeta = cargo.query(
    CATEGORY_FILTER_TABLE .. "=cat",
    'name, filterVal, ordering',
    {
      where = string.format('tab="%s" AND filterField="%s"', typeData.tab, typeData.filterField),
      groupBy = 'cat.filterVal'
    }
  )
  local categories = {}
  for _, cat in ipairs(categoriesMeta) do
    local name, val, order = cat.name, cat.filterVal, cat.ordering
    local wherePart = string.format('%s="%s" AND luaId NOT LIKE "%%attack%%"', typeData.filterField, val)
    if typeData.recipeType then
      wherePart = wherePart .. string.format(' AND recipeType="%s"', typeData.recipeType)
    end

    local foundObjects = cargo.query(
      typeData.cargo_table,
      'name',
      {
        where = wherePart,
      }
    )
    local foundNames = {}
    for _, row in ipairs(foundObjects) do
      table.insert(foundNames, row.name)
    end
    categories[name] = { ordering = tonumber(order) or 0, names = foundNames }
  end

  return categories
end

---@param type string
---@return table<string, CategoryData>
nav.queryUserExtrasCategories =  function(type)
  local userCategoriesRows = cargo.query(
    USER_NAV_CATEGORIES_TABLE,
    'category=catName, pagename',
    {
      where = string.format('UPPER(type) = "%s"', type)
    }
  )
  local categories = {}
  for _, row in ipairs(userCategoriesRows) do
    local catName = row.catName;
    if not categories[catName] then
      categories[catName] = { ordering = 999, names = {} }
    end

    table.insert(categories[catName].names, row.pagename)
  end

  return categories
end

-- Names in extra have priority.
-- Does mutate base
---@param base table<string, CategoryData>
---@param extra table<string, CategoryData>
---@return table<string, CategoryData>
nav.mergeCategories = function (base, extra)
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
nav.sortCategories = function(categories)
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
nav.createNavBox = function(tableTitle, rawType)
  ---@type NavboxType
  local type = mw.ustring.upper(rawType or "")
  local typeData = TYPES[type]
  if not typeData then
    return string.format("Navbox error: Unknown type: '%s'", type)
  end

  local frame = mw.getCurrentFrame()

  local baseCategories = nav.queryBaseCategories(typeData)
  local extraCategories = nav.queryUserExtrasCategories(type)

  local categories = nav.mergeCategories(baseCategories, extraCategories)
  -- mw.logObject(categories) 
  nav.removeEmptyCategories(categories)

  local sortedCategories = nav.sortCategories(categories)

  local rowsHtml = ""
  for _, cat in pairs(sortedCategories) do
    local objects = "" -- list of objects to insert in a row
    for _, name in ipairs(cat.data.names) do
      objects = objects .. stripWhitespace(frame:expandTemplate { title = "NavboxIconLinkNamed", args = { name = name } })
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
  return nav.createNavBox(title, rawType)
end

return p



--[[
Debugging:

local frame = { args = { title = "Buildings", type = "Building" } }
(enter)
= p.create(frame, "Buildings", "Building")
(enter)

Resources:
General cargo: https://www.mediawiki.org/wiki/Extension:Cargo/Querying_data
Cargo querying from LUA: https://www.mediawiki.org/wiki/Extension:Cargo/Other_features#Lua_support
https://www.mediawiki.org/wiki/Extension:Scribunto/Lua_reference_manual

--]]
