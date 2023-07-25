<?php

require_once 'vendor/autoload.php';

use Opis\JsonSchema\{
    Validator
};

$STARTED = false;

$validator = new Validator();
$resolver = $validator->loader()->resolver();

function start($request)
{
    if ($request->version !== 1) {
        throw new Exception('Wrong version!');
    }

    $GLOBALS['STARTED'] = true;

    $response = [
        'ready' => true,
        'version' => 1,
        'implementation' => [
            'language' => 'php',
            'name' => 'json-schema',
            'homepage' => 'https://opis.io/json-schema',
            'issues' => 'https://github.com/opis/json-schema/issues',
            'dialects' => [
                'http://json-schema.org/draft/2020-12/schema#',
                'http://json-schema.org/draft-2019-09/schema#',
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
    if (!$GLOBALS['STARTED']) {
        throw new Exception('Not started!');
    }
    return json_encode(['ok' => true]);
}

function run($request)
{
    if (!$GLOBALS['STARTED']) {
        throw new Exception('Not started!');
    }

    $registry = json_decode($request->case->registry);

    if ($registry != null) {
        foreach ($registry as $key => $value) {
            $GLOBALS['resolver']->registerRaw($value, $key);
        }
    }

    $results = [];

    foreach ($request->case->tests as $test) {
        $result = $GLOBALS['validator']->validate(json_decode($test->instance), json_decode($request->case->schema));
        $results[] = ['valid' => $result->isValid()];
    }
    $response = ['seq' => $request->seq, 'results' => $results];
    return json_encode($response);
}

function stop($request)
{
    if (!$GLOBALS['STARTED']) {
        throw new Exception('Not started!');
    }

    exit(0);
}

$cmds = [
    'start' => 'start',
    'dialect' => 'dialect',
    'run' => 'run',
    'stop' => 'stop'
];

while (($line = fgets(STDIN)) !== false) {
    $request = json_decode($line);
    if (json_last_error() !== JSON_ERROR_NONE) {
        echo json_encode(['error' => 'Invalid JSON']) . "\n";
        continue;
    }

    $cmd = $request->cmd;

    try {
        $response = $cmds[$cmd]($request);
        echo $response . "\n";
    } catch (Exception $e) {
        echo json_encode(['error' => $e->getMessage()]) . "\n";
    }
}
