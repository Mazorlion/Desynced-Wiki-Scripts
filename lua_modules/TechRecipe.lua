local p = {}
local m = {} -- Use for internal function. You can use this one for debugging without exposing functions, return this instead of p

---@type any
---@diagnostic disable-next-line: lowercase-global
mw = mw

-- Mirror tech cargo table
---@class TechCargo
---@field name string
---@field luaId string
---@field description string
---@field category string
---@field texture string
---@field requiredTech1 string
---@field requiredTech2 string
---@field requiredTech3 string
---@field progressCount integer
---@field ingredient1 string
---@field amount1 integer
---@field ingredient2 string
---@field amount2 integer
---@field ingredient3 string
---@field amount3 integer
---@field ingredient4 string
---@field amount4 integer
---@field producer1 string
---@field time1 number
---@field producer2 string
---@field time2 number
---@field producer3 string
---@field time3 number
---@field producer4 string
---@field time4 number
---@field recipeType string
---@field numProduced integer

---@param name string
function m.get_tech_cargo_data(name)
    local fields = "name, luaId, description, category, texture, " ..
                   "requiredTech1, requiredTech2, requiredTech3, " ..
                   "progressCount, " ..
                   "ingredient1, amount1, " ..
                   "ingredient2, amount2, " ..
                   "ingredient3, amount3, " ..
                   "ingredient4, amount4, " ..
                   "producer1, time1, " ..
                   "producer2, time2, " ..
                   "producer3, time3, " ..
                   "producer4, time4, " ..
                   "recipeType, numProduced"

    local results = mw.ext.cargo.query(
        "tech",
        fields,
        { where = string.format("name = '%s'", name) }
    )

    if not results or not results[1] then
        return nil
    end

    local row = results[1]

    local numericFields = {
        "progressCount",
        "amount1", "amount2", "amount3", "amount4",
        "time1", "time2", "time3", "time4",
        "numProduced"
    }
    for _, f in ipairs(numericFields) do
        row[f] = tonumber(row[f]) or 0
    end
    if row.numProduced == 0 then
        row.numProduced = 1
    end

    ---@cast row TechCargo
    return row
end

-- Inserts a table row cell for a single ingredient
---@param tech TechCargo The tech cargo object
---@param i integer Ingredient index (1–4)
---@param craft_count integer Amount multiplier
---@return nil 
m.ingredient_cell =  function(row, tech, i, craft_count)
    local ing = tech["ingredient" .. i]
    ---@type integer
    local amt = (tech["amount" .. i]) * craft_count

    if not ing or ing == "" then
        row:tag("td"):done()
        return
    end

    row:tag("td")
        :wikitext(string.format(
            "[[File:%s.png|64x64px|link=%s|alt=%s]] %i",
            ing, ing, ing, amt
        )):done()
end

---@param parent table
---@return nil 
m.researched_with_header_row = function(parent)
    local headerRow = parent:tag("tr")
    headerRow:tag("th"):wikitext("Building/Component"):done()
    headerRow:tag("th"):wikitext("Research time"):done()
    headerRow:done()
end

-- Insert a 6 cells header
---@param parent table
---@param tech TechCargo
---@return nil 
m.ingredients_header_row = function(parent, tech)
    local headerRow = parent:tag("tr")
    for i = 1, 4 do
        if tech["ingredient"..i] and tech["ingredient"..i] ~= "" then
            headerRow:tag("th"):wikitext(string.format("[[%s]]", tech["ingredient"..i])):done()
        end
    end
    -- Empty cell, for arrow under it
    headerRow:tag("th"):done()
    headerRow:tag("th"):wikitext(tech.name):done()
    headerRow:done()
end

-- Insert a 6 cells row
---@param parent table
---@param tech TechCargo
---@param craft_count integer Multiply all counts by this
---@return nil 
m.ingredients_rows = function(parent, tech, craft_count)
    local dataRow = parent:tag("tr")
    for i = 1, 4 do
        m.ingredient_cell(dataRow, tech, i, craft_count)
    end
    dataRow:tag("td"):wikitext("[[File:Arrow_Right.png|link=Arrow Right|alt=Arrow Right|32x32px]]"):done()
    dataRow:tag("td"):wikitext(string.format("[[File:%s.png|64x64px|link=Technology/%s|alt=%s]] %i",
        tech.name, tech.name, tech.name, tech.numProduced * craft_count)):done()
    dataRow:done()
end

---@param tech TechCargo
---@return string
m.recipe_table = function(tech)
    local elem = mw.html.create("table")
    elem
        :addClass("wikitable")
        :tag("caption"):wikitext("Recipe"):done()

    m.ingredients_header_row(elem, tech)
    m.ingredients_rows(elem, tech, 1)
    return tostring(elem)
end

-- Partial mirror of cargo table component
---@class RecipeUplink
---@field name string
---@field uplinkRate number

--- Get name of frame
---@param lua_id string
---@return string|nil
m.get_frame_name = function(lua_id)
    local results = mw.ext.cargo.query(
        "entity",
        "name", 
        { where = string.format("luaId = '%s'", lua_id) }
    )
    if results and #results > 0 then
        return results[1].name
    end
    return nil
end

--- Replace some components with their building (by lua id). Only supports frame
--- Or hide them if nil
local UPLINK_REPLACEMENTS = {
    c_alien_research = "f_alien_researcher"
}

---@return RecipeUplink[]
m.get_uplinks = function()
    local uplinks = {}

    local results = mw.ext.cargo.query(
        "component",
        "name, luaId, uplinkRate",                    -- fields list
        { where ="uplinkRate != 0",
        orderBy = "uplinkRate DESC"} -- To try get the most basics first
    )

    for _, obj in ipairs(results) do
        local replacement_id = UPLINK_REPLACEMENTS[obj.luaId]
        local new_name = replacement_id and m.get_frame_name(replacement_id)
        if new_name ~= nil then
            obj.name = new_name
        end

        ---@type RecipeUplink
        local uplink = { name = obj.name, uplinkRate = tonumber(obj.uplinkRate) or 1 }
        table.insert(uplinks, uplink)
    end
    return uplinks
end

---@param parent table
---@param tech TechCargo
---@return nil
m.researched_with_rows = function(parent, tech)
    -- Research are different than usual recipes in that they only have one shared recipe, only the speed changes
    -- We list the speed for each exiting uplinks component
    for _, uplink in ipairs(m.get_uplinks()) do
        local name = uplink.name
        local production_time = uplink.uplinkRate * tech.time1

        local text = string.format(
            "[[File:%s.png|64x64px|link=%s|alt=%s]][[%s]]",
            name, name, name, name
        ) 
        local dataRow = parent:tag("tr")
        dataRow:tag("td"):wikitext(text):done()
        if production_time ~= 0 then
            dataRow:tag("td"):wikitext(string.format("%i seconds", production_time)):done()
        else
            dataRow:tag("td"):done()
        end
        dataRow:done()
    end

end

---@param tech TechCargo
---@return string
m.researched_with_table = function(tech)
    local elem = mw.html.create("table")
    elem
        :addClass("wikitable")
        :tag("caption"):wikitext("Researched with"):done()

    m.researched_with_header_row(elem)
    m.researched_with_rows(elem, tech)

    return tostring(elem)
end

---@param tech TechCargo
---@return string
m.total_requirements_table = function(tech)
    local elem = mw.html.create("table")
    elem
        :addClass("wikitable")
        :tag("caption"):wikitext("Total Requirements"):done()

    m.ingredients_header_row(elem, tech)
    local required_count = math.ceil(tech.progressCount / tech.numProduced)
    m.ingredients_rows(elem, tech, required_count) -- / could be round_up(tech.progressCount / tech.numProduced), but numProduced seems to be always 1
    return tostring(elem)
end

--- Main function
---@param name string
---@return string
m.render = function(name)
    local tech = m.get_tech_cargo_data(name)
    if not tech then
        return "(Recipe not found)"
    end

    local result = 
          m.recipe_table(tech)
      ..  m.researched_with_table(tech)
      ..  m.total_requirements_table(tech)

    return result
end

p.render = function (frame)
    return m.render(frame.args.name)
end

return p

--[[
Debugging:

Return m instead of p if you want to debug those private functions

local frame = { args = { name = "Ultra-tech Framework" } }
(enter)
= p.render(frame)
(enter)

--]]
