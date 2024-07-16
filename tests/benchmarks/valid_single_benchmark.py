def get_benchmark():
    return dict(
        name="benchmark",
        schema={
            "type": "object",
        },
        description="benchmark",
        tests=[
            {
                "description": "test",
                "instance": {
                    "a": "b",
                },
            },
        ],
    )
