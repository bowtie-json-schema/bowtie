local jsonschema = require 'jsonschema'
local json = require 'json'

STARTED = false

io.stdout:setvbuf 'no'

local handle = io.popen 'luarocks show jsonschema --mversion'
local jsonschema_version = handle:read '*a'
handle:close()

local cmds = {
  start = function(request)
    assert(request.version == 1, 'Wrong version!')
    STARTED = true
    return {
      ready = true,
      version = 1,
      implementation = {
        language = 'lua',
        name = 'jsonschema',
        version = jsonschema_version,
        homepage = 'https://github.com/api7/jsonschema',
        issues = 'https://github.com/api7/jsonschema/issues',

        dialects = {
          'http://json-schema.org/draft-07/schema#',
          'http://json-schema.org/draft-06/schema#',
          'http://json-schema.org/draft-04/schema#',
        },
      },
    }
  end,
  dialect = function(_)
    assert(STARTED, 'Not started!')
    return { ok = false }
  end,
  run = function(request)
    assert(STARTED, 'Not started!')

    local validate = jsonschema.generate_validator(request.case.schema, {
      external_resolver = function(url)
        return request.case.registry[url]
      end,
    })
    local results = {}
    for _, test in ipairs(request.case.tests) do
      table.insert(results, { valid = validate(test.instance) })
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
