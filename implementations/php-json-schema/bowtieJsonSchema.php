<?php

$STARTED = false;

$cmds = [
    'start' => function($request) use (&$STARTED) {
        assert($request['version'] == 1, 'Wrong version!');
        $STARTED = true;
        return [
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
                    ,
                ],
            ],
        ];
    },

    'stop' => function() use (&$STARTED) {
        assert($STARTED, 'Not started!');
        exit(0);
    },
];

while ($line = fgets(STDIN)) {
    $request = json_decode($line, true);
    $response = $cmds[$request['cmd']]($request);
    fwrite(STDOUT, json_encode($response) . "\n");
}
