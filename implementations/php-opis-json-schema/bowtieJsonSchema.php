<?php

require_once 'vendor/autoload.php';

use Opis\JsonSchema\{
    Validator
};

$STARTED = false;

function start($request)
{
    assert($request->version == 1, 'Wrong version!');

    $GLOBALS['STARTED'] = true;


    $jsonschema_version = "<error reading composer data>";
    $composer = json_decode(file_get_contents('vendor/composer/installed.json'));
    foreach ($composer->packages as $package) {
        if ($package->name == "opis/json-schema") {
            $jsonschema_version = $package->version;
            break;
        }
    }

    return [
        'ready' => true,
        'version' => 1,
        'implementation' => [
            'language' => 'php',
            'name' => 'opis-json-schema',
            'version' => $jsonschema_version,
            'homepage' => 'https://opis.io/json-schema',
            'issues' => 'https://github.com/opis/json-schema/issues',
            'dialects' => [
                'https://json-schema.org/draft/2020-12/schema',
                'https://json-schema.org/draft-2019-09/schema',
                'http://json-schema.org/draft-07/schema#',
                'http://json-schema.org/draft-06/schema#',
            ],
            'os' => PHP_OS,
            'os_version' => php_uname('r'),
            'language_version' => PHP_VERSION,
        ],
    ];
    return json_encode($response);
}

function dialect($request)
{
    assert($GLOBALS['STARTED'], 'Not started!');
    return json_encode(['ok' => false]);
}

function run($request)
{
    assert($GLOBALS['STARTED'], 'Not started!');

    $validator = new Validator();
    $resolver = $validator->loader()->resolver();

    if (isset($request->case->registry)) {
        foreach ($request->case->registry as $key => $value) {
            $resolver->registerRaw($value, $key);
        }
    }

    $results = [];

    foreach ($request->case->tests as $test) {
        try {
            $result = $validator->validate($test->instance, $request->case->schema);
            $results[] = ['valid' => $result->isValid()];
        } catch (Exception $e) {
            $results[] = [
                'errored' => true,
                'context' => ['message' => $e->getMessage()],
            ];
        }
    }
    $response = ['seq' => $request->seq, 'results' => $results];
    return json_encode($response);
}

function stop($request)
{
    assert($GLOBALS['STARTED'], 'Not started!');
    exit(0);
}

$cmds = [
    'start' => 'start',
    'dialect' => 'dialect',
    'run' => 'run',
    'stop' => 'stop'
];

while (true) {
    $request = json_decode(fgets(STDIN));
    $cmd = $request->cmd;
    $response = $cmds[$cmd]($request);
    echo $response . "\n";
}
