<?php

require_once 'vendor/autoload.php';

use Opis\JsonSchema\{
    Validator,
    SchemaLoader,
};

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

function stop($request)
{
    if (!$GLOBALS['STARTED']) {
        throw new Exception('Not started!');
    }

    exit(0);
}

$cmds = [
    'start' => 'start',
    'stop' => 'stop',
];

$STARTED = false;

while (($line = fgets(STDIN)) !== false) {
    $request = json_decode($line);
    if (json_last_error() !== JSON_ERROR_NONE) {
        echo json_encode(['error' => 'Invalid JSON']) . "\n";
        continue;
    }

    $cmd = $request->cmd;

    try {
        $response = $cmd($request);
        echo $response . "\n";
    } catch (Exception $e) {
        echo json_encode(['error' => $e->getMessage()]) . "\n";
    }
}
