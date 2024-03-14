local jsonschema = require 'jsonschema'
local json = require 'json'

STARTED = false

io.stdout:setvbuf 'no'

local handle = io.popen 'luarocks show jsonschema --mversion'
local jsonschema_version = handle:read '*a'
handle:close()

local function resolve_in_registry(registry)
  return function(url)
    return registry[url]
  end
end

local cmds = {
  start = function(request)
    assert(request.version == 1, 'Wrong version!')
    STARTED = true
    local os_platform_handle = io.popen 'uname'
    local os_platform = os_platform_handle:read '*l'
    os_platform_handle:close()

    local os_version_handle = io.popen 'uname -r'
    local os_version = os_version_handle:read '*l'
    os_version_handle:close()

    local lua_version = (function()
      local temp = {}
      for str in _VERSION:gmatch '%S+' do
        table.insert(temp, str)
      end
      return temp[2]
    end)()

    return {
      version = 1,
      implementation = {
        language = 'lua',
        name = 'jsonschema',
        version = jsonschema_version,
        homepage = 'https://github.com/api7/jsonschema',
        issues = 'https://github.com/api7/jsonschema/issues',
        source = 'https://github.com/api7/jsonschema',

        dialects = {
          'http://json-schema.org/draft-07/schema#',
          'http://json-schema.org/draft-06/schema#',
          'http://json-schema.org/draft-04/schema#',
        },
        os = os_platform,
        os_version = os_version,
        language_version = lua_version,
      },
    }
  end,
  dialect = function(_)
    assert(STARTED, 'Not started!')
    return { ok = false }
  end,
  run = function(request)
    assert(STARTED, 'Not started!')

    local registry = request.case.registry
    local opts = { external_resolver = resolve_in_registry(registry) }
    local ok, result = xpcall(jsonschema.generate_validator, debug.traceback, request.case.schema, opts)
    if not ok then
      return {
        seq = request.seq,
        errored = true,
        context = { traceback = result },
      }
    end
    local results = {}
    for _, test in ipairs(request.case.tests) do
      table.insert(results, { valid = result(test.instance) })
    end
    return { seq = request.seq, results = results }
  end,
  stop = function(_)
    assert(STARTED, 'Not started!')
    os.exit(0)
  end,
}

local request, response
for line in io.lines() do
  request = json.decode(line)
  response = cmds[request.cmd](request)
  io.write(json.encode(response) .. '\n')
end
