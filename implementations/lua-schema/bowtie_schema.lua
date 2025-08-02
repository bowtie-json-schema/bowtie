local schema = require('schema')
local json = require('dkjson')

local modnames = {
    ['https://json-schema.org/draft/2020-12/schema'] = 'schema.draft2020-12',
    ['https://json-schema.org/draft/2019-09/schema'] = 'schema.draft2019-09',
    ['http://json-schema.org/draft-07/schema#'] = 'schema.draft-07',
    ['http://json-schema.org/draft-06/schema#'] = 'schema.draft-06',
    ['http://json-schema.org/draft-04/schema#'] = 'schema.draft-04',
}

local function exec (cmd)
    local f = io.popen(cmd)
    local line = f:read('*l')
    f:close()
    return line
end

local STARTED = false

local cmds = {
    start = function (request)
        assert(request.version == 1, 'Wrong version!')
        STARTED = true
        return {
            version = 1,
            implementation = {
                language = 'lua',
                name = schema._NAME,
                version = schema._VERSION,
                homepage = 'https://fperrad.frama.io/lua-schema',
                issues = 'https://framagit.org/fperrad/lua-schema/-/issues',
                source = 'https://framagit.org/fperrad/lua-schema',
                dialects = {
                    'https://json-schema.org/draft/2020-12/schema',
                    'https://json-schema.org/draft/2019-09/schema',
                    'http://json-schema.org/draft-07/schema#',
                    'http://json-schema.org/draft-06/schema#',
                    'http://json-schema.org/draft-04/schema#',
                },
                os = exec('uname'),
                os_version = exec('uname -r'),
                language_version = _VERSION:match('^%S+%s+(%S+)'),
            },
        }
    end,
    dialect = function (request)
        assert(STARTED, 'Not started!')
        local modname = modnames[request.dialect]
        if modname then
            require(modname)
            return {
                ok = true,
            }
        else
            return {
                ok = false,
            }
        end
    end,
    run = function (request)
        assert(STARTED, 'Not started!')
        local case = request.case
        schema.custom_resolver = function (url)
            if case.registry then
                return case.registry[url]
            end
        end
        local ok, validator = xpcall(schema.new, debug.traceback, case.schema)
        if not ok then
            return {
                errored = true,
                seq = request.seq,
                context = {
                    traceback = validator,
                },
            }
        end
        local results = {}
        for i = 1, #case.tests do
            results[i] = validator:validate(case.tests[i].instance)
        end
        return {
            seq = request.seq,
            results = results,
        }
    end,
    stop = function ()
        assert(STARTED, 'Not started!')
        os.exit(0)
    end,
}

io.stdout:setvbuf('no')
for line in io.lines() do
    local request = json.decode(line)
    local fn = cmds[request.cmd]
    local response = fn(request)
    io.write(json.encode(response) .. '\n')
end
