<?php

ini_set('display_errors', 'stderr');

require_once 'vendor/autoload.php';

use Opis\JsonSchema\{
    Validator
};

$STARTED = false;
$CURRENT_DIALECT = NULL;

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
        'version' => 1,
        'implementation' => [
            'language' => 'php',
            'name' => 'opis-json-schema',
            'version' => $jsonschema_version,
            'homepage' => 'https://opis.io/json-schema',
            'documentation' => 'https://opis.io/json-schema/2.x/',
            'source' => 'https://github.com/opis/json-schema',
            'issues' => 'https://github.com/opis/json-schema/issues',
            'dialects' => [
                'https://json-schema.org/draft/2020-12/schema',
                'https://json-schema.org/draft/2019-09/schema',
                'http://json-schema.org/draft-07/schema#',
                'http://json-schema.org/draft-06/schema#',
            ],
            'os' => PHP_OS,
            'os_version' => php_uname('r'),
            'language_version' => PHP_VERSION,
        ],
    ];
}

function dialect($request)
{
    assert($GLOBALS['STARTED'], 'Not started!');
    // These seem to be magic values the implementation understands.
    // See e.g. https://github.com/opis/json-schema/blob/c48df6d7089a45f01e1c82432348f2d5976f9bfb/tests/AbstractOfficialDraftTest.php#L69
    $dialects = [
        'https://json-schema.org/draft/2020-12/schema' => '2020-12',
        'https://json-schema.org/draft/2019-09/schema' => '2019-09',
        'http://json-schema.org/draft-07/schema#' => '07',
        'http://json-schema.org/draft-06/schema#' => '06',
    ];
    $GLOBALS['CURRENT_DIALECT'] = $dialects[$request->dialect];
    return ['ok' => true];
}

function run($request)
{
    assert($GLOBALS['STARTED'], 'Not started!');

    $validator = new Validator();
    if (isset($request->case->registry)) {
        $resolver = $validator->loader()->resolver();
        foreach ($request->case->registry as $key => $value) {
            $resolver->registerRaw($value, $key);
        }
    }

    $results = [];

    foreach ($request->case->tests as $test) {
        try {
            $result = $validator->dataValidation(
                $test->instance,
                $request->case->schema,
                null,
                null,
                null,
                $GLOBALS['CURRENT_DIALECT'],
            );
            $results[] = ['valid' => $result == NULL];
        } catch (Exception $e) {
            $results[] = [
                'errored' => true,
                'context' => [
                    'message' => $e->getMessage(),
                    'traceback' => $e->getTraceAsString(),
                ],
            ];
        }
    }
    return ['seq' => $request->seq, 'results' => $results];
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
    $response = $cmds[$request->cmd]($request);
    echo json_encode($response) . "\n";
}
