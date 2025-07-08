### 1. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "properties": {
    "foo": {},
    "bar": {}
  },
  "patternProperties": {
    "^v": {}
  },
  "additionalProperties": false
}

### Results:
| Instance | swift-json-schema (swift) |
|:------------------------------------:|:-------:|
|              {"foo": 1}              |  valid  |
| {"foo": 1, "bar": 2, "quux": "boom"} | invalid |
|              [1, 2, 3]               |  valid  |
|             "foobarbaz"              |  valid  |
|                  12                  |  valid  |
|        {"foo": 1, "vroom": 2}        |  valid  |### 2. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "patternProperties": {
    "^\u00e1": {}
  },
  "additionalProperties": false
}

### Results:
| Instance | swift-json-schema (swift) |
|:-------------------------:|:-------:|
| {"\u00e1rm\u00e1nyos": 2} |  valid  |
|  {"\u00e9lm\u00e9ny": 2}  | invalid |### 3. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "properties": {
    "foo": {},
    "bar": {}
  },
  "additionalProperties": {
    "type": "boolean"
  }
}

### Results:
| Instance | swift-json-schema (swift) |
|:----------------------------------:|:-------:|
|             {"foo": 1}             |  valid  |
| {"foo": 1, "bar": 2, "quux": true} |  valid  |
|  {"foo": 1, "bar": 2, "quux": 12}  | invalid |### 4. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "additionalProperties": {
    "type": "boolean"
  }
}

### Results:
| Instance | swift-json-schema (swift) |
|:-------------:|:-------:|
| {"foo": true} |  valid  |
|   {"foo": 1}  | invalid |### 5. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "properties": {
    "foo": {},
    "bar": {}
  }
}

### Results:
| Instance | swift-json-schema (swift) |
|:----------------------------------:|:-----:|
| {"foo": 1, "bar": 2, "quux": true} | valid |### 6. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "allOf": [
    {
      "properties": {
        "foo": {}
      }
    }
  ],
  "additionalProperties": {
    "type": "boolean"
  }
}

### Results:
| Instance | swift-json-schema (swift) |
|:-----------------------:|:-------:|
| {"foo": 1, "bar": true} | invalid |### 7. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "additionalProperties": {
    "type": "null"
  }
}

### Results:
| Instance | swift-json-schema (swift) |
|:-------------:|:-----:|
| {"foo": null} | valid |### 8. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "propertyNames": {
    "maxLength": 5
  },
  "additionalProperties": {
    "type": "number"
  }
}

### Results:
| Instance | swift-json-schema (swift) |
|:-------------------------------:|:-------:|
|           {"apple": 4}          |  valid  |
| {"fig": 2, "pear": "available"} | invalid |### 9. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "properties": {
    "foo2": {}
  },
  "dependentSchemas": {
    "foo": {},
    "foo2": {
      "properties": {
        "bar": {}
      }
    }
  },
  "additionalProperties": false
}

### Results:
| Instance | swift-json-schema (swift) |
|:-----------------------:|:-------:|
|       {"foo": ""}       | invalid |
|       {"bar": ""}       | invalid |
| {"foo2": "", "bar": ""} | invalid |### 10. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "allOf": [
    {
      "properties": {
        "bar": {
          "type": "integer"
        }
      },
      "required": [
        "bar"
      ]
    },
    {
      "properties": {
        "foo": {
          "type": "string"
        }
      },
      "required": [
        "foo"
      ]
    }
  ]
}

### Results:
| Instance | swift-json-schema (swift) |
|:-----------------------------:|:-------:|
|    {"foo": "baz", "bar": 2}   |  valid  |
|         {"foo": "baz"}        | invalid |
|           {"bar": 2}          | invalid |
| {"foo": "baz", "bar": "quux"} | invalid |### 11. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "properties": {
    "bar": {
      "type": "integer"
    }
  },
  "required": [
    "bar"
  ],
  "allOf": [
    {
      "properties": {
        "foo": {
          "type": "string"
        }
      },
      "required": [
        "foo"
      ]
    },
    {
      "properties": {
        "baz": {
          "type": "null"
        }
      },
      "required": [
        "baz"
      ]
    }
  ]
}

### Results:
| Instance | swift-json-schema (swift) |
|:--------------------------------------:|:-------:|
| {"foo": "quux", "bar": 2, "baz": null} |  valid  |
|      {"foo": "quux", "baz": null}      | invalid |
|        {"bar": 2, "baz": null}         | invalid |
|       {"foo": "quux", "bar": 2}        | invalid |
|               {"bar": 2}               | invalid |### 12. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "allOf": [
    {
      "maximum": 30
    },
    {
      "minimum": 20
    }
  ]
}

### Results:
| Instance | swift-json-schema (swift) |
|:--:|:-------:|
| 25 |  valid  |
| 35 | invalid |### 13. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "allOf": [
    true,
    true
  ]
}

### Results:
| Instance | swift-json-schema (swift) |
|:-----:|:-----:|
| "foo" | valid |### 14. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "allOf": [
    true,
    false
  ]
}

### Results:
| Instance | swift-json-schema (swift) |
|:-----:|:-------:|
| "foo" | invalid |### 15. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "allOf": [
    false,
    false
  ]
}

### Results:
| Instance | swift-json-schema (swift) |
|:-----:|:-------:|
| "foo" | invalid |### 16. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "allOf": [
    {}
  ]
}

### Results:
| Instance | swift-json-schema (swift) |
|:-:|:-----:|
| 1 | valid |### 17. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "allOf": [
    {},
    {}
  ]
}

### Results:
| Instance | swift-json-schema (swift) |
|:-:|:-----:|
| 1 | valid |### 18. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "allOf": [
    {},
    {
      "type": "number"
    }
  ]
}

### Results:
| Instance | swift-json-schema (swift) |
|:-----:|:-------:|
|   1   |  valid  |
| "foo" | invalid |### 19. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "allOf": [
    {
      "type": "number"
    },
    {}
  ]
}

### Results:
| Instance | swift-json-schema (swift) |
|:-----:|:-------:|
|   1   |  valid  |
| "foo" | invalid |### 20. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "allOf": [
    {
      "allOf": [
        {
          "type": "null"
        }
      ]
    }
  ]
}

### Results:
| Instance | swift-json-schema (swift) |
|:----:|:-------:|
| null |  valid  |
| 123  | invalid |### 21. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "allOf": [
    {
      "multipleOf": 2
    }
  ],
  "anyOf": [
    {
      "multipleOf": 3
    }
  ],
  "oneOf": [
    {
      "multipleOf": 5
    }
  ]
}

### Results:
| Instance | swift-json-schema (swift) |
|:--:|:-------:|
| 1  | invalid |
| 5  | invalid |
| 3  | invalid |
| 15 | invalid |
| 2  | invalid |
| 10 | invalid |
| 6  | invalid |
| 30 |  valid  |### 22. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$ref": "#foo",
  "$defs": {
    "A": {
      "$anchor": "foo",
      "type": "integer"
    }
  }
}

### Results:
| Instance | swift-json-schema (swift) |
|:---:|:-------:|
|  1  |  valid  |
| "a" | invalid |### 23. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$ref": "http://localhost:1234/draft2020-12/bar#foo",
  "$defs": {
    "A": {
      "$id": "http://localhost:1234/draft2020-12/bar",
      "$anchor": "foo",
      "type": "integer"
    }
  }
}

### Results:
| Instance | swift-json-schema (swift) |
|:---:|:-------:|
|  1  |  valid  |
| "a" | invalid |### 24. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "http://localhost:1234/draft2020-12/root",
  "$ref": "http://localhost:1234/draft2020-12/nested.json#foo",
  "$defs": {
    "A": {
      "$id": "nested.json",
      "$defs": {
        "B": {
          "$anchor": "foo",
          "type": "integer"
        }
      }
    }
  }
}

### Results:
| Instance | swift-json-schema (swift) |
|:---:|:-------:|
|  1  |  valid  |
| "a" | invalid |### 25. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "http://localhost:1234/draft2020-12/foobar",
  "$defs": {
    "A": {
      "$id": "child1",
      "allOf": [
        {
          "$id": "child2",
          "$anchor": "my_anchor",
          "type": "number"
        },
        {
          "$anchor": "my_anchor",
          "type": "string"
        }
      ]
    }
  },
  "$ref": "child1#my_anchor"
}

### Results:
| Instance | swift-json-schema (swift) |
|:---:|:-------:|
| "a" |  valid  |
|  1  | invalid |### 26. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "anyOf": [
    {
      "type": "integer"
    },
    {
      "minimum": 2
    }
  ]
}

### Results:
| Instance | swift-json-schema (swift) |
|:---:|:-------:|
|  1  |  valid  |
| 2.5 |  valid  |
|  3  |  valid  |
| 1.5 | invalid |### 27. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "string",
  "anyOf": [
    {
      "maxLength": 2
    },
    {
      "minLength": 4
    }
  ]
}

### Results:
| Instance | swift-json-schema (swift) |
|:--------:|:-------:|
|    3     | invalid |
| "foobar" |  valid  |
|  "foo"   | invalid |### 28. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "anyOf": [
    true,
    true
  ]
}

### Results:
| Instance | swift-json-schema (swift) |
|:-----:|:-----:|
| "foo" | valid |### 29. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "anyOf": [
    true,
    false
  ]
}

### Results:
| Instance | swift-json-schema (swift) |
|:-----:|:-----:|
| "foo" | valid |### 30. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "anyOf": [
    false,
    false
  ]
}

### Results:
| Instance | swift-json-schema (swift) |
|:-----:|:-------:|
| "foo" | invalid |### 31. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "anyOf": [
    {
      "properties": {
        "bar": {
          "type": "integer"
        }
      },
      "required": [
        "bar"
      ]
    },
    {
      "properties": {
        "foo": {
          "type": "string"
        }
      },
      "required": [
        "foo"
      ]
    }
  ]
}

### Results:
| Instance | swift-json-schema (swift) |
|:-------------------------:|:-------:|
|         {"bar": 2}        |  valid  |
|       {"foo": "baz"}      |  valid  |
|  {"foo": "baz", "bar": 2} |  valid  |
| {"foo": 2, "bar": "quux"} | invalid |### 32. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "anyOf": [
    {
      "type": "number"
    },
    {}
  ]
}

### Results:
| Instance | swift-json-schema (swift) |
|:-----:|:-----:|
| "foo" | valid |
|  123  | valid |### 33. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "anyOf": [
    {
      "anyOf": [
        {
          "type": "null"
        }
      ]
    }
  ]
}

### Results:
| Instance | swift-json-schema (swift) |
|:----:|:-------:|
| null |  valid  |
| 123  | invalid |### 34. Schema:
 true

### Results:
| Instance | swift-json-schema (swift) |
|:--------------:|:-----:|
|       1        | valid |
|     "foo"      | valid |
|      true      | valid |
|     false      | valid |
|      null      | valid |
| {"foo": "bar"} | valid |
|       {}       | valid |
|    ["foo"]     | valid |
|       []       | valid |### 35. Schema:
 false

### Results:
| Instance | swift-json-schema (swift) |
|:--------------:|:-------:|
|       1        | invalid |
|     "foo"      | invalid |
|      true      | invalid |
|     false      | invalid |
|      null      | invalid |
| {"foo": "bar"} | invalid |
|       {}       | invalid |
|    ["foo"]     | invalid |
|       []       | invalid |### 36. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "const": 2
}

### Results:
| Instance | swift-json-schema (swift) |
|:---:|:-------:|
|  2  |  valid  |
|  5  | invalid |
| "a" | invalid |### 37. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "const": {
    "foo": "bar",
    "baz": "bax"
  }
}

### Results:
| Instance | swift-json-schema (swift) |
|:----------------------------:|:-------:|
| {"foo": "bar", "baz": "bax"} |  valid  |
| {"baz": "bax", "foo": "bar"} |  valid  |
|        {"foo": "bar"}        | invalid |
|            [1, 2]            | invalid |### 38. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "const": [
    {
      "foo": "bar"
    }
  ]
}

### Results:
| Instance | swift-json-schema (swift) |
|:----------------:|:-------:|
| [{"foo": "bar"}] |  valid  |
|       [2]        | invalid |
|    [1, 2, 3]     | invalid |### 39. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "const": null
}

### Results:
| Instance | swift-json-schema (swift) |
|:----:|:-------:|
| null |  valid  |
|  0   | invalid |### 40. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "const": false
}

### Results:
| Instance | swift-json-schema (swift) |
|:-----:|:-------:|
| false |  valid  |
|   0   | invalid |
|  0.0  | invalid |### 41. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "const": true
}

### Results:
| Instance | swift-json-schema (swift) |
|:----:|:-------:|
| true |  valid  |
|  1   | invalid |
| 1.0  | invalid |### 42. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "const": [
    false
  ]
}

### Results:
| Instance | swift-json-schema (swift) |
|:-------:|:-------:|
|  |  valid  |
|   [0]   | invalid |
|  [0.0]  | invalid |### 43. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "const": [
    true
  ]
}

### Results:
| Instance | swift-json-schema (swift) |
|:------:|:-------:|
|  |  valid  |
|  [1]   | invalid |
| [1.0]  | invalid |### 44. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "const": {
    "a": false
  }
}

### Results:
| Instance | swift-json-schema (swift) |
|:------------:|:-------:|
| {"a": false} |  valid  |
|   {"a": 0}   | invalid |
|  {"a": 0.0}  | invalid |### 45. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "const": {
    "a": true
  }
}

### Results:
| Instance | swift-json-schema (swift) |
|:-----------:|:-------:|
| {"a": true} |  valid  |
|   {"a": 1}  | invalid |
|  {"a": 1.0} | invalid |### 46. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "const": 0
}

### Results:
| Instance | swift-json-schema (swift) |
|:-----:|:-------:|
| false | invalid |
|   0   |  valid  |
|  0.0  |  valid  |
|   {}  | invalid |
|   []  | invalid |
|   ""  | invalid |### 47. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "const": 1
}

### Results:
| Instance | swift-json-schema (swift) |
|:----:|:-------:|
| true | invalid |
|  1   |  valid  |
| 1.0  |  valid  |### 48. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "const": -2.0
}

### Results:
| Instance | swift-json-schema (swift) |
|:--------:|:-------:|
|    -2    |  valid  |
|    2     | invalid |
|   -2.0   |  valid  |
|   2.0    | invalid |
| -2.00001 | invalid |### 49. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "const": 9007199254740992
}

### Results:
| Instance | swift-json-schema (swift) |
|:------------------:|:-------:|
|  9007199254740992  |  valid  |
|  9007199254740991  | invalid |
| 9007199254740992.0 |  valid  |
| 9007199254740991.0 | invalid |### 50. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "const": "hello\u0000there"
}

### Results:
| Instance | swift-json-schema (swift) |
|:------------------:|:-------:|
| "hello\u0000there" |  valid  |
|    "hellothere"    | invalid |### 51. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "contains": {
    "minimum": 5
  }
}

### Results:
| Instance | swift-json-schema (swift) |
|:------------:|:-------:|
|  [3, 4, 5]   |  valid  |
|  [3, 4, 6]   |  valid  |
| [3, 4, 5, 6] |  valid  |
|  [2, 3, 4]   | invalid |
|      []      | invalid |
|      {}      |  valid  |### 52. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "contains": {
    "const": 5
  }
}

### Results:
| Instance | swift-json-schema (swift) |
|:------------:|:-------:|
|  [3, 4, 5]   |  valid  |
| [3, 4, 5, 5] |  valid  |
| [1, 2, 3, 4] | invalid |### 53. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "contains": true
}

### Results:
| Instance | swift-json-schema (swift) |
|:-------:|:-------:|
| ["foo"] |  valid  |
|    []   | invalid |### 54. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "contains": false
}

### Results:
| Instance | swift-json-schema (swift) |
|:------------------------------------:|:-------:|
|               ["foo"]                | invalid |
|                  []                  | invalid |
| "contains does not apply to strings" |  valid  |### 55. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "items": {
    "multipleOf": 2
  },
  "contains": {
    "multipleOf": 3
  }
}

### Results:
| Instance | swift-json-schema (swift) |
|:---------:|:-------:|
| [2, 4, 8] | invalid |
| [3, 6, 9] | invalid |
|  [6, 12]  |  valid  |
|   [1, 5]  | invalid |### 56. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "contains": {
    "if": false,
    "else": true
  }
}

### Results:
| Instance | swift-json-schema (swift) |
|:-------:|:-------:|
| ["foo"] |  valid  |
|    []   | invalid |### 57. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "contains": {
    "type": "null"
  }
}

### Results:
| Instance | swift-json-schema (swift) |
|:------:|:-----:|
|  | valid |### 58. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "contentMediaType": "application/json"
}

### Results:
| Instance | swift-json-schema (swift) |
|:--------------------:|:-----:|
| "{\"foo\": \"bar\"}" | valid |
|        "{:}"         | valid |
|         100          | valid |### 59. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "contentEncoding": "base64"
}

### Results:
| Instance | swift-json-schema (swift) |
|:----------------------:|:-----:|
| "eyJmb28iOiAiYmFyIn0K" | valid |
| "eyJmb28iOi%iYmFyIn0K" | valid |
|          100           | valid |### 60. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "contentMediaType": "application/json",
  "contentEncoding": "base64"
}

### Results:
| Instance | swift-json-schema (swift) |
|:----------------------:|:-----:|
| "eyJmb28iOiAiYmFyIn0K" | valid |
|       "ezp9Cg=="       | valid |
|          "{}"          | valid |
|          100           | valid |### 61. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "contentMediaType": "application/json",
  "contentEncoding": "base64",
  "contentSchema": {
    "type": "object",
    "required": [
      "foo"
    ],
    "properties": {
      "foo": {
        "type": "string"
      }
    }
  }
}

### Results:
| Instance | swift-json-schema (swift) |
|:--------------------------------------:|:-----:|
|         "eyJmb28iOiAiYmFyIn0K"         | valid |
| "eyJib28iOiAyMCwgImZvbyI6ICJiYXoifQ==" | valid |
|           "eyJib28iOiAyMH0="           | valid |
|                 "e30="                 | valid |
|                 "W10="                 | valid |
|               "ezp9Cg=="               | valid |
|                  "{}"                  | valid |
|                  100                   | valid |### 62. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "properties": {
    "foo": {
      "type": "integer",
      "default": []
    }
  }
}

### Results:
| Instance | swift-json-schema (swift) |
|:-----------:|:-----:|
| {"foo": 13} | valid |
|      {}     | valid |### 63. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "properties": {
    "bar": {
      "type": "string",
      "minLength": 4,
      "default": "bad"
    }
  }
}

### Results:
| Instance | swift-json-schema (swift) |
|:---------------:|:-----:|
| {"bar": "good"} | valid |
|        {}       | valid |### 64. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "properties": {
    "alpha": {
      "type": "number",
      "maximum": 3,
      "default": 5
    }
  }
}

### Results:
| Instance | swift-json-schema (swift) |
|:------------:|:-------:|
| {"alpha": 1} |  valid  |
| {"alpha": 5} | invalid |
|      {}      |  valid  |### 65. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$ref": "https://json-schema.org/draft/2020-12/schema"
}

### Results:
| Instance | swift-json-schema (swift) |
|:---------------------------------------:|:-----:|
| {"$defs": {"foo": {"type": "integer"}}} | error |
|     {"$defs": {"foo": {"type": 1}}}     | error |### 66. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "dependentRequired": {
    "bar": [
      "foo"
    ]
  }
}

### Results:
| Instance | swift-json-schema (swift) |
|:--------------------:|:-------:|
|          {}          |  valid  |
|      {"foo": 1}      |  valid  |
| {"foo": 1, "bar": 2} |  valid  |
|      {"bar": 2}      | invalid |
|       ["bar"]        |  valid  |
|       "foobar"       |  valid  |
|          12          |  valid  |### 67. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "dependentRequired": {
    "bar": []
  }
}

### Results:
| Instance | swift-json-schema (swift) |
|:----------:|:-----:|
|     {}     | valid |
| {"bar": 2} | valid |
|     1      | valid |### 68. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "dependentRequired": {
    "quux": [
      "foo",
      "bar"
    ]
  }
}

### Results:
| Instance | swift-json-schema (swift) |
|:-------------------------------:|:-------:|
|                {}               |  valid  |
|       {"foo": 1, "bar": 2}      |  valid  |
| {"foo": 1, "bar": 2, "quux": 3} |  valid  |
|      {"foo": 1, "quux": 2}      | invalid |
|      {"bar": 1, "quux": 2}      | invalid |
|           {"quux": 1}           | invalid |### 69. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "dependentRequired": {
    "foo\nbar": [
      "foo\rbar"
    ],
    "foo\"bar": [
      "foo'bar"
    ]
  }
}

### Results:
| Instance | swift-json-schema (swift) |
|:------------------------------:|:-------:|
| {"foo\nbar": 1, "foo\rbar": 2} |  valid  |
| {"foo'bar": 1, "foo\"bar": 2}  |  valid  |
|   {"foo\nbar": 1, "foo": 2}    | invalid |
|        {"foo\"bar": 2}         | invalid |### 70. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "dependentSchemas": {
    "bar": {
      "properties": {
        "foo": {
          "type": "integer"
        },
        "bar": {
          "type": "integer"
        }
      }
    }
  }
}

### Results:
| Instance | swift-json-schema (swift) |
|:------------------------------:|:-------:|
|      {"foo": 1, "bar": 2}      |  valid  |
|        {"foo": "quux"}         |  valid  |
|   {"foo": "quux", "bar": 2}    | invalid |
|   {"foo": 2, "bar": "quux"}    | invalid |
| {"foo": "quux", "bar": "quux"} | invalid |
|            ["bar"]             |  valid  |
|            "foobar"            |  valid  |
|               12               |  valid  |### 71. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "dependentSchemas": {
    "foo": true,
    "bar": false
  }
}

### Results:
| Instance | swift-json-schema (swift) |
|:--------------------:|:-------:|
|      {"foo": 1}      |  valid  |
|      {"bar": 2}      | invalid |
| {"foo": 1, "bar": 2} | invalid |
|          {}          |  valid  |### 72. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "dependentSchemas": {
    "foo\tbar": {
      "minProperties": 4
    },
    "foo'bar": {
      "required": [
        "foo\"bar"
      ]
    }
  }
}

### Results:
| Instance | swift-json-schema (swift) |
|:---------------------------------------:|:-------:|
| {"foo\tbar": 1, "a": 2, "b": 3, "c": 4} |  valid  |
|       {"foo'bar": {"foo\"bar": 1}}      | invalid |
|         {"foo\tbar": 1, "a": 2}         | invalid |
|              {"foo'bar": 1}             | invalid |### 73. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "properties": {
    "foo": {}
  },
  "dependentSchemas": {
    "foo": {
      "properties": {
        "bar": {}
      },
      "additionalProperties": false
    }
  }
}

### Results:
| Instance | swift-json-schema (swift) |
|:--------------------:|:-------:|
|      {"foo": 1}      | invalid |
|      {"bar": 1}      |  valid  |
| {"foo": 1, "bar": 2} | invalid |
|      {"baz": 1}      |  valid  |### 74. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://test.json-schema.org/dynamicRef-dynamicAnchor-same-schema/root",
  "type": "array",
  "items": {
    "$dynamicRef": "#items"
  },
  "$defs": {
    "foo": {
      "$dynamicAnchor": "items",
      "type": "string"
    }
  }
}

### Results:
| Instance | swift-json-schema (swift) |
|:--------------:|:-------:|
| ["foo", "bar"] |  valid  |
|  ["foo", 42]   | invalid |### 75. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://test.json-schema.org/dynamicRef-anchor-same-schema/root",
  "type": "array",
  "items": {
    "$dynamicRef": "#items"
  },
  "$defs": {
    "foo": {
      "$anchor": "items",
      "type": "string"
    }
  }
}

### Results:
| Instance | swift-json-schema (swift) |
|:--------------:|:-------:|
| ["foo", "bar"] |  valid  |
|  ["foo", 42]   | invalid |### 76. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://test.json-schema.org/ref-dynamicAnchor-same-schema/root",
  "type": "array",
  "items": {
    "$ref": "#items"
  },
  "$defs": {
    "foo": {
      "$dynamicAnchor": "items",
      "type": "string"
    }
  }
}

### Results:
| Instance | swift-json-schema (swift) |
|:--------------:|:-------:|
| ["foo", "bar"] |  valid  |
|  ["foo", 42]   | invalid |### 77. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://test.json-schema.org/typical-dynamic-resolution/root",
  "$ref": "list",
  "$defs": {
    "foo": {
      "$dynamicAnchor": "items",
      "type": "string"
    },
    "list": {
      "$id": "list",
      "type": "array",
      "items": {
        "$dynamicRef": "#items"
      },
      "$defs": {
        "items": {
          "$comment": "This is only needed to satisfy the bookending requirement",
          "$dynamicAnchor": "items"
        }
      }
    }
  }
}

### Results:
| Instance | swift-json-schema (swift) |
|:--------------:|:-----:|
| ["foo", "bar"] | valid |
|  ["foo", 42]   | valid |### 78. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://test.json-schema.org/dynamicRef-without-anchor/root",
  "$ref": "list",
  "$defs": {
    "foo": {
      "$dynamicAnchor": "items",
      "type": "string"
    },
    "list": {
      "$id": "list",
      "type": "array",
      "items": {
        "$dynamicRef": "#/$defs/items"
      },
      "$defs": {
        "items": {
          "$comment": "This is only needed to satisfy the bookending requirement",
          "$dynamicAnchor": "items",
          "type": "number"
        }
      }
    }
  }
}

### Results:
| Instance | swift-json-schema (swift) |
|:--------------:|:-------:|
| ["foo", "bar"] | invalid |
|    [24, 42]    |  valid  |### 79. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://test.json-schema.org/dynamic-resolution-with-intermediate-scopes/root",
  "$ref": "intermediate-scope",
  "$defs": {
    "foo": {
      "$dynamicAnchor": "items",
      "type": "string"
    },
    "intermediate-scope": {
      "$id": "intermediate-scope",
      "$ref": "list"
    },
    "list": {
      "$id": "list",
      "type": "array",
      "items": {
        "$dynamicRef": "#items"
      },
      "$defs": {
        "items": {
          "$comment": "This is only needed to satisfy the bookending requirement",
          "$dynamicAnchor": "items"
        }
      }
    }
  }
}

### Results:
| Instance | swift-json-schema (swift) |
|:--------------:|:-----:|
| ["foo", "bar"] | valid |
|  ["foo", 42]   | valid |### 80. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://test.json-schema.org/dynamic-resolution-ignores-anchors/root",
  "$ref": "list",
  "$defs": {
    "foo": {
      "$anchor": "items",
      "type": "string"
    },
    "list": {
      "$id": "list",
      "type": "array",
      "items": {
        "$dynamicRef": "#items"
      },
      "$defs": {
        "items": {
          "$comment": "This is only needed to satisfy the bookending requirement",
          "$dynamicAnchor": "items"
        }
      }
    }
  }
}

### Results:
| Instance | swift-json-schema (swift) |
|:-----------:|:-----:|
| ["foo", 42] | valid |### 81. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://test.json-schema.org/dynamic-resolution-without-bookend/root",
  "$ref": "list",
  "$defs": {
    "foo": {
      "$dynamicAnchor": "items",
      "type": "string"
    },
    "list": {
      "$id": "list",
      "type": "array",
      "items": {
        "$dynamicRef": "#items"
      },
      "$defs": {
        "items": {
          "$comment": "This is only needed to give the reference somewhere to resolve to when it behaves like $ref",
          "$anchor": "items"
        }
      }
    }
  }
}

### Results:
| Instance | swift-json-schema (swift) |
|:-----------:|:-----:|
| ["foo", 42] | valid |### 82. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://test.json-schema.org/unmatched-dynamic-anchor/root",
  "$ref": "list",
  "$defs": {
    "foo": {
      "$dynamicAnchor": "items",
      "type": "string"
    },
    "list": {
      "$id": "list",
      "type": "array",
      "items": {
        "$dynamicRef": "#items"
      },
      "$defs": {
        "items": {
          "$comment": "This is only needed to give the reference somewhere to resolve to when it behaves like $ref",
          "$anchor": "items",
          "$dynamicAnchor": "foo"
        }
      }
    }
  }
}

### Results:
| Instance | swift-json-schema (swift) |
|:-----------:|:-----:|
| ["foo", 42] | valid |### 83. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://test.json-schema.org/relative-dynamic-reference/root",
  "$dynamicAnchor": "meta",
  "type": "object",
  "properties": {
    "foo": {
      "const": "pass"
    }
  },
  "$ref": "extended",
  "$defs": {
    "extended": {
      "$id": "extended",
      "$dynamicAnchor": "meta",
      "type": "object",
      "properties": {
        "bar": {
          "$ref": "bar"
        }
      }
    },
    "bar": {
      "$id": "bar",
      "type": "object",
      "properties": {
        "baz": {
          "$dynamicRef": "extended#meta"
        }
      }
    }
  }
}

### Results:
| Instance | swift-json-schema (swift) |
|:------------------------------------------------:|:-----:|
| {"foo": "pass", "bar": {"baz": {"foo": "pass"}}} | valid |
| {"foo": "pass", "bar": {"baz": {"foo": "fail"}}} | valid |### 84. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://test.json-schema.org/relative-dynamic-reference-without-bookend/root",
  "$dynamicAnchor": "meta",
  "type": "object",
  "properties": {
    "foo": {
      "const": "pass"
    }
  },
  "$ref": "extended",
  "$defs": {
    "extended": {
      "$id": "extended",
      "$anchor": "meta",
      "type": "object",
      "properties": {
        "bar": {
          "$ref": "bar"
        }
      }
    },
    "bar": {
      "$id": "bar",
      "type": "object",
      "properties": {
        "baz": {
          "$dynamicRef": "extended#meta"
        }
      }
    }
  }
}

### Results:
| Instance | swift-json-schema (swift) |
|:------------------------------------------------:|:-------:|
| {"foo": "pass", "bar": {"baz": {"foo": "fail"}}} | invalid |### 85. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://test.json-schema.org/dynamic-ref-with-multiple-paths/main",
  "if": {
    "properties": {
      "kindOfList": {
        "const": "numbers"
      }
    },
    "required": [
      "kindOfList"
    ]
  },
  "then": {
    "$ref": "numberList"
  },
  "else": {
    "$ref": "stringList"
  },
  "$defs": {
    "genericList": {
      "$id": "genericList",
      "properties": {
        "list": {
          "items": {
            "$dynamicRef": "#itemType"
          }
        }
      },
      "$defs": {
        "defaultItemType": {
          "$comment": "Only needed to satisfy bookending requirement",
          "$dynamicAnchor": "itemType"
        }
      }
    },
    "numberList": {
      "$id": "numberList",
      "$defs": {
        "itemType": {
          "$dynamicAnchor": "itemType",
          "type": "number"
        }
      },
      "$ref": "genericList"
    },
    "stringList": {
      "$id": "stringList",
      "$defs": {
        "itemType": {
          "$dynamicAnchor": "itemType",
          "type": "string"
        }
      },
      "$ref": "genericList"
    }
  }
}

### Results:
| Instance | swift-json-schema (swift) |
|:------------------------------------------:|:-----:|
|  {"kindOfList": "numbers", "list": [1.1]}  | valid |
| {"kindOfList": "numbers", "list": ["foo"]} | valid |
|  {"kindOfList": "strings", "list": [1.1]}  | valid |
| {"kindOfList": "strings", "list": ["foo"]} | valid |### 86. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://test.json-schema.org/dynamic-ref-leaving-dynamic-scope/main",
  "if": {
    "$id": "first_scope",
    "$defs": {
      "thingy": {
        "$comment": "this is first_scope#thingy",
        "$dynamicAnchor": "thingy",
        "type": "number"
      }
    }
  },
  "then": {
    "$id": "second_scope",
    "$ref": "start",
    "$defs": {
      "thingy": {
        "$comment": "this is second_scope#thingy, the final destination of the $dynamicRef",
        "$dynamicAnchor": "thingy",
        "type": "null"
      }
    }
  },
  "$defs": {
    "start": {
      "$comment": "this is the landing spot from $ref",
      "$id": "start",
      "$dynamicRef": "inner_scope#thingy"
    },
    "thingy": {
      "$comment": "this is the first stop for the $dynamicRef",
      "$id": "inner_scope",
      "$dynamicAnchor": "thingy",
      "type": "string"
    }
  }
}

### Results:
| Instance | swift-json-schema (swift) |
|:----------:|:-------:|
| "a string" |  valid  |
|     42     | invalid |
|    null    | invalid |### 87. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "http://localhost:1234/draft2020-12/strict-tree.json",
  "$dynamicAnchor": "node",
  "$ref": "tree.json",
  "unevaluatedProperties": false
}

### Results:
| Instance | swift-json-schema (swift) |
|:---------------------------:|:-------:|
| {"children": [{"daat": 1}]} | invalid |
| {"children": [{"data": 1}]} | invalid |### 88. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "http://localhost:1234/draft2020-12/strict-extendible.json",
  "$ref": "extendible-dynamic-ref.json",
  "$defs": {
    "elements": {
      "$dynamicAnchor": "elements",
      "properties": {
        "a": true
      },
      "required": [
        "a"
      ],
      "additionalProperties": false
    }
  }
}

### Results:
| Instance | swift-json-schema (swift) |
|:------------------------:|:-------:|
|       {"a": true}        | invalid |
| {"elements": [{"b": 1}]} |  valid  |
| {"elements": [{"a": 1}]} |  valid  |### 89. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "http://localhost:1234/draft2020-12/strict-extendible-allof-defs-first.json",
  "allOf": [
    {
      "$ref": "extendible-dynamic-ref.json"
    },
    {
      "$defs": {
        "elements": {
          "$dynamicAnchor": "elements",
          "properties": {
            "a": true
          },
          "required": [
            "a"
          ],
          "additionalProperties": false
        }
      }
    }
  ]
}

### Results:
| Instance | swift-json-schema (swift) |
|:------------------------:|:-------:|
|       {"a": true}        | invalid |
| {"elements": [{"b": 1}]} |  valid  |
| {"elements": [{"a": 1}]} |  valid  |### 90. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "http://localhost:1234/draft2020-12/strict-extendible-allof-ref-first.json",
  "allOf": [
    {
      "$defs": {
        "elements": {
          "$dynamicAnchor": "elements",
          "properties": {
            "a": true
          },
          "required": [
            "a"
          ],
          "additionalProperties": false
        }
      }
    },
    {
      "$ref": "extendible-dynamic-ref.json"
    }
  ]
}

### Results:
| Instance | swift-json-schema (swift) |
|:------------------------:|:-------:|
|       {"a": true}        | invalid |
| {"elements": [{"b": 1}]} |  valid  |
| {"elements": [{"a": 1}]} |  valid  |### 91. Schema:
 {
  "$ref": "http://localhost:1234/draft2020-12/detached-dynamicref.json#/$defs/foo"
}

### Results:
| Instance | swift-json-schema (swift) |
|:---:|:-------:|
|  1  |  valid  |
| "a" | invalid |### 92. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$defs": {
    "true": true,
    "false": false
  },
  "properties": {
    "true": {
      "$dynamicRef": "#/$defs/true"
    },
    "false": {
      "$dynamicRef": "#/$defs/false"
    }
  }
}

### Results:
| Instance | swift-json-schema (swift) |
|:------------:|:-------:|
| {"true": 1}  |  valid  |
| {"false": 1} | invalid |### 93. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://test.json-schema.org/dynamic-ref-skips-intermediate-resource/main",
  "type": "object",
  "properties": {
    "bar-item": {
      "$ref": "item"
    }
  },
  "$defs": {
    "bar": {
      "$id": "bar",
      "type": "array",
      "items": {
        "$ref": "item"
      },
      "$defs": {
        "item": {
          "$id": "item",
          "type": "object",
          "properties": {
            "content": {
              "$dynamicRef": "#content"
            }
          },
          "$defs": {
            "defaultContent": {
              "$dynamicAnchor": "content",
              "type": "integer"
            }
          }
        },
        "content": {
          "$dynamicAnchor": "content",
          "type": "string"
        }
      }
    }
  }
}

### Results:
| Instance | swift-json-schema (swift) |
|:----------------------------------:|:-------:|
|   {"bar-item": {"content": 42}}    |  valid  |
| {"bar-item": {"content": "value"}} | invalid |### 94. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "enum": [
    1,
    2,
    3
  ]
}

### Results:
| Instance | swift-json-schema (swift) |
|:-:|:-------:|
| 1 |  valid  |
| 4 | invalid |### 95. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "enum": [
    6,
    "foo",
    [],
    true,
    {
      "foo": 12
    }
  ]
}

### Results:
| Instance | swift-json-schema (swift) |
|:----------------------:|:-------:|
|           []           |  valid  |
|          null          | invalid |
|     {"foo": false}     | invalid |
|      {"foo": 12}       |  valid  |
| {"foo": 12, "boo": 42} | invalid |### 96. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "enum": [
    6,
    null
  ]
}

### Results:
| Instance | swift-json-schema (swift) |
|:------:|:-------:|
|  null  |  valid  |
|   6    |  valid  |
| "test" | invalid |### 97. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "properties": {
    "foo": {
      "enum": [
        "foo"
      ]
    },
    "bar": {
      "enum": [
        "bar"
      ]
    }
  },
  "required": [
    "bar"
  ]
}

### Results:
| Instance | swift-json-schema (swift) |
|:-----------------------------:|:-------:|
|  {"foo": "foo", "bar": "bar"} |  valid  |
| {"foo": "foot", "bar": "bar"} | invalid |
| {"foo": "foo", "bar": "bart"} | invalid |
|         {"bar": "bar"}        |  valid  |
|         {"foo": "foo"}        | invalid |
|               {}              | invalid |### 98. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "enum": [
    "foo\nbar",
    "foo\rbar"
  ]
}

### Results:
| Instance | swift-json-schema (swift) |
|:----------:|:-------:|
| "foo\nbar" |  valid  |
| "foo\rbar" |  valid  |
|   "abc"    | invalid |### 99. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "enum": [
    false
  ]
}

### Results:
| Instance | swift-json-schema (swift) |
|:-----:|:-------:|
| false |  valid  |
|   0   | invalid |
|  0.0  | invalid |### 100. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "enum": [
    [
      false
    ]
  ]
}

### Results:
| Instance | swift-json-schema (swift) |
|:-------:|:-------:|
|  |  valid  |
|   [0]   | invalid |
|  [0.0]  | invalid |### 101. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "enum": [
    true
  ]
}

### Results:
| Instance | swift-json-schema (swift) |
|:----:|:-------:|
| true |  valid  |
|  1   | invalid |
| 1.0  | invalid |### 102. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "enum": [
    [
      true
    ]
  ]
}

### Results:
| Instance | swift-json-schema (swift) |
|:------:|:-------:|
|  |  valid  |
|  [1]   | invalid |
| [1.0]  | invalid |### 103. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "enum": [
    0
  ]
}

### Results:
| Instance | swift-json-schema (swift) |
|:-----:|:-------:|
| false | invalid |
|   0   |  valid  |
|  0.0  |  valid  |### 104. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "enum": [
    [
      0
    ]
  ]
}

### Results:
| Instance | swift-json-schema (swift) |
|:-------:|:-------:|
|  | invalid |
|   [0]   |  valid  |
|  [0.0]  |  valid  |### 105. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "enum": [
    1
  ]
}

### Results:
| Instance | swift-json-schema (swift) |
|:----:|:-------:|
| true | invalid |
|  1   |  valid  |
| 1.0  |  valid  |### 106. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "enum": [
    [
      1
    ]
  ]
}

### Results:
| Instance | swift-json-schema (swift) |
|:------:|:-------:|
|  | invalid |
|  [1]   |  valid  |
| [1.0]  |  valid  |### 107. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "enum": [
    "hello\u0000there"
  ]
}

### Results:
| Instance | swift-json-schema (swift) |
|:------------------:|:-------:|
| "hello\u0000there" |  valid  |
|    "hellothere"    | invalid |### 108. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "exclusiveMaximum": 3.0
}

### Results:
| Instance | swift-json-schema (swift) |
|:---:|:-------:|
| 2.2 |  valid  |
| 3.0 | invalid |
| 3.5 | invalid |
| "x" |  valid  |### 109. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "exclusiveMinimum": 1.1
}

### Results:
| Instance | swift-json-schema (swift) |
|:---:|:-------:|
| 1.2 |  valid  |
| 1.1 | invalid |
| 0.6 | invalid |
| "x" |  valid  |### 110. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "format": "email"
}

### Results:
| Instance | swift-json-schema (swift) |
|:------:|:-----:|
|   12   | valid |
|  13.7  | valid |
|   {}   | valid |
|   []   | valid |
| false  | valid |
|  null  | valid |
| "2962" | valid |### 111. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "format": "idn-email"
}

### Results:
| Instance | swift-json-schema (swift) |
|:------:|:-----:|
|   12   | valid |
|  13.7  | valid |
|   {}   | valid |
|   []   | valid |
| false  | valid |
|  null  | valid |
| "2962" | valid |### 112. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "format": "regex"
}

### Results:
| Instance | swift-json-schema (swift) |
|:--------:|:-----:|
|    12    | valid |
|   13.7   | valid |
|    {}    | valid |
|    []    | valid |
|  false   | valid |
|   null   | valid |
| "^(abc]" | valid |### 113. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "format": "ipv4"
}

### Results:
| Instance | swift-json-schema (swift) |
|:-------------:|:-----:|
|       12      | valid |
|      13.7     | valid |
|       {}      | valid |
|       []      | valid |
|     false     | valid |
|      null     | valid |
| "127.0.0.0.1" | valid |### 114. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "format": "ipv6"
}

### Results:
| Instance | swift-json-schema (swift) |
|:---------:|:-----:|
|     12    | valid |
|    13.7   | valid |
|     {}    | valid |
|     []    | valid |
|   false   | valid |
|    null   | valid |
| "12345::" | valid |### 115. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "format": "idn-hostname"
}

### Results:
| Instance | swift-json-schema (swift) |
|:---------------------------------------:|:-----:|
|                    12                   | valid |
|                   13.7                  | valid |
|                    {}                   | valid |
|                    []                   | valid |
|                  false                  | valid |
|                   null                  | valid |
| "\u302e\uc2e4\ub840.\ud14c\uc2a4\ud2b8" | valid |### 116. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "format": "hostname"
}

### Results:
| Instance | swift-json-schema (swift) |
|:---------------------------------:|:-----:|
|                 12                | valid |
|                13.7               | valid |
|                 {}                | valid |
|                 []                | valid |
|               false               | valid |
|                null               | valid |
| "-a-host-name-that-starts-with--" | valid |### 117. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "format": "date"
}

### Results:
| Instance | swift-json-schema (swift) |
|:------------:|:-----:|
|      12      | valid |
|     13.7     | valid |
|      {}      | valid |
|      []      | valid |
|    false     | valid |
|     null     | valid |
| "06/19/1963" | valid |### 118. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "format": "date-time"
}

### Results:
| Instance | swift-json-schema (swift) |
|:-------------------------------:|:-----:|
|                12               | valid |
|               13.7              | valid |
|                {}               | valid |
|                []               | valid |
|              false              | valid |
|               null              | valid |
| "1990-02-31T15:59:60.123-08:00" | valid |### 119. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "format": "time"
}

### Results:
| Instance | swift-json-schema (swift) |
|:--------------:|:-----:|
|       12       | valid |
|      13.7      | valid |
|       {}       | valid |
|       []       | valid |
|     false      | valid |
|      null      | valid |
| "08:30:06 PST" | valid |### 120. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "format": "json-pointer"
}

### Results:
| Instance | swift-json-schema (swift) |
|:-----------:|:-----:|
|      12     | valid |
|     13.7    | valid |
|      {}     | valid |
|      []     | valid |
|    false    | valid |
|     null    | valid |
| "/foo/bar~" | valid |### 121. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "format": "relative-json-pointer"
}

### Results:
| Instance | swift-json-schema (swift) |
|:----------:|:-----:|
|     12     | valid |
|    13.7    | valid |
|     {}     | valid |
|     []     | valid |
|   false    | valid |
|    null    | valid |
| "/foo/bar" | valid |### 122. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "format": "iri"
}

### Results:
| Instance | swift-json-schema (swift) |
|:------------------------------------------------:|:-----:|
|                        12                        | valid |
|                       13.7                       | valid |
|                        {}                        | valid |
|                        []                        | valid |
|                      false                       | valid |
|                       null                       | valid |
| "http://2001:0db8:85a3:0000:0000:8a2e:0370:7334" | valid |### 123. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "format": "iri-reference"
}

### Results:
| Instance | swift-json-schema (swift) |
|:-------------------------------------------:|:-----:|
|                      12                     | valid |
|                     13.7                    | valid |
|                      {}                     | valid |
|                      []                     | valid |
|                    false                    | valid |
|                     null                    | valid |
| "\\\\WINDOWS\\fil\u00eb\u00df\u00e5r\u00e9" | valid |### 124. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "format": "uri"
}

### Results:
| Instance | swift-json-schema (swift) |
|:-------------------------:|:-----:|
|             12            | valid |
|            13.7           | valid |
|             {}            | valid |
|             []            | valid |
|           false           | valid |
|            null           | valid |
| "//foo.bar/?baz=qux#quux" | valid |### 125. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "format": "uri-reference"
}

### Results:
| Instance | swift-json-schema (swift) |
|:------------------------:|:-----:|
|            12            | valid |
|           13.7           | valid |
|            {}            | valid |
|            []            | valid |
|          false           | valid |
|           null           | valid |
| "\\\\WINDOWS\\fileshare" | valid |### 126. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "format": "uri-template"
}

### Results:
| Instance | swift-json-schema (swift) |
|:----------------------------------------------:|:-----:|
|                       12                       | valid |
|                      13.7                      | valid |
|                       {}                       | valid |
|                       []                       | valid |
|                     false                      | valid |
|                      null                      | valid |
| "http://example.com/dictionary/{term:1}/{term" | valid |### 127. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "format": "uuid"
}

### Results:
| Instance | swift-json-schema (swift) |
|:-------------------------------------:|:-----:|
|                   12                  | valid |
|                  13.7                 | valid |
|                   {}                  | valid |
|                   []                  | valid |
|                 false                 | valid |
|                  null                 | valid |
| "2eb8aa08-aa98-11ea-b4aa-73b441d1638" | valid |### 128. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "format": "duration"
}

### Results:
| Instance | swift-json-schema (swift) |
|:------:|:-----:|
|   12   | valid |
|  13.7  | valid |
|   {}   | valid |
|   []   | valid |
| false  | valid |
|  null  | valid |
| "PT1D" | valid |### 129. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "if": {
    "const": 0
  }
}

### Results:
| Instance | swift-json-schema (swift) |
|:-------:|:-----:|
|    0    | valid |
| "hello" | valid |### 130. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "then": {
    "const": 0
  }
}

### Results:
| Instance | swift-json-schema (swift) |
|:-------:|:-----:|
|    0    | valid |
| "hello" | valid |### 131. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "else": {
    "const": 0
  }
}

### Results:
| Instance | swift-json-schema (swift) |
|:-------:|:-----:|
|    0    | valid |
| "hello" | valid |### 132. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "if": {
    "exclusiveMaximum": 0
  },
  "then": {
    "minimum": -10
  }
}

### Results:
| Instance | swift-json-schema (swift) |
|:----:|:-------:|
|  -1  |  valid  |
| -100 | invalid |
|  3   |  valid  |### 133. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "if": {
    "exclusiveMaximum": 0
  },
  "else": {
    "multipleOf": 2
  }
}

### Results:
| Instance | swift-json-schema (swift) |
|:--:|:-------:|
| -1 |  valid  |
| 4  |  valid  |
| 3  | invalid |### 134. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "if": {
    "exclusiveMaximum": 0
  },
  "then": {
    "minimum": -10
  },
  "else": {
    "multipleOf": 2
  }
}

### Results:
| Instance | swift-json-schema (swift) |
|:----:|:-------:|
|  -1  |  valid  |
| -100 | invalid |
|  4   |  valid  |
|  3   | invalid |### 135. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "allOf": [
    {
      "if": {
        "exclusiveMaximum": 0
      }
    },
    {
      "then": {
        "minimum": -10
      }
    },
    {
      "else": {
        "multipleOf": 2
      }
    }
  ]
}

### Results:
| Instance | swift-json-schema (swift) |
|:----:|:-----:|
| -100 | valid |
|  3   | valid |### 136. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "if": true,
  "then": {
    "const": "then"
  },
  "else": {
    "const": "else"
  }
}

### Results:
| Instance | swift-json-schema (swift) |
|:------:|:-------:|
| "then" |  valid  |
| "else" | invalid |### 137. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "if": false,
  "then": {
    "const": "then"
  },
  "else": {
    "const": "else"
  }
}

### Results:
| Instance | swift-json-schema (swift) |
|:------:|:-------:|
| "then" | invalid |
| "else" |  valid  |### 138. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "then": {
    "const": "yes"
  },
  "else": {
    "const": "other"
  },
  "if": {
    "maxLength": 4
  }
}

### Results:
| Instance | swift-json-schema (swift) |
|:---------:|:-------:|
|   "yes"   |  valid  |
|  "other"  |  valid  |
|    "no"   | invalid |
| "invalid" | invalid |### 139. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$defs": {
    "int": {
      "type": "integer"
    }
  },
  "allOf": [
    {
      "properties": {
        "foo": {
          "$ref": "#/$defs/int"
        }
      }
    },
    {
      "additionalProperties": {
        "$ref": "#/$defs/int"
      }
    }
  ]
}

### Results:
| Instance | swift-json-schema (swift) |
|:-------------------:|:-------:|
|      {"foo": 1}     |  valid  |
| {"foo": "a string"} | invalid |### 140. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "items": {
    "type": "integer"
  }
}

### Results:
| Instance | swift-json-schema (swift) |
|:-----------------------------:|:-------:|
|           [1, 2, 3]           |  valid  |
|            [1, "x"]           | invalid |
|         {"foo": "bar"}        |  valid  |
| {"0": "invalid", "length": 1} |  valid  |### 141. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "items": true
}

### Results:
| Instance | swift-json-schema (swift) |
|:----------------:|:-----:|
| [1, "foo", true] | valid |
|        []        | valid |### 142. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "items": false
}

### Results:
| Instance | swift-json-schema (swift) |
|:----------------:|:-------:|
| [1, "foo", true] | invalid |
|        []        |  valid  |### 143. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$defs": {
    "item": {
      "type": "array",
      "items": false,
      "prefixItems": [
        {
          "$ref": "#/$defs/sub-item"
        },
        {
          "$ref": "#/$defs/sub-item"
        }
      ]
    },
    "sub-item": {
      "type": "object",
      "required": [
        "foo"
      ]
    }
  },
  "type": "array",
  "items": false,
  "prefixItems": [
    {
      "$ref": "#/$defs/item"
    },
    {
      "$ref": "#/$defs/item"
    },
    {
      "$ref": "#/$defs/item"
    }
  ]
}

### Results:
| Instance | swift-json-schema (swift) |
|:--------------------------------------------------------------------------------------------------------------------------------:|:-------:|
|                 [[{"foo": null}, {"foo": null}], [{"foo": null}, {"foo": null}], [{"foo": null}, {"foo": null}]]                 |  valid  |
| [[{"foo": null}, {"foo": null}], [{"foo": null}, {"foo": null}], [{"foo": null}, {"foo": null}], [{"foo": null}, {"foo": null}]] | invalid |
|         [[{"foo": null}, {"foo": null}, {"foo": null}], [{"foo": null}, {"foo": null}], [{"foo": null}, {"foo": null}]]          | invalid |
|                         [{"foo": null}, [{"foo": null}, {"foo": null}], [{"foo": null}, {"foo": null}]]                          | invalid |
|                      [[{}, {"foo": null}], [{"foo": null}, {"foo": null}], [{"foo": null}, {"foo": null}]]                       | invalid |
|                                                [[{"foo": null}], [{"foo": null}]]                                                |  valid  |### 144. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "array",
  "items": {
    "type": "array",
    "items": {
      "type": "array",
      "items": {
        "type": "array",
        "items": {
          "type": "number"
        }
      }
    }
  }
}

### Results:
| Instance | swift-json-schema (swift) |
|:------------------------------------------:|:-------:|
|  [[[[1]], [[2], [3]]], [[[4], [5], [6]]]]  |  valid  |
| [[[["1"]], [[2], [3]]], [[[4], [5], [6]]]] | invalid |
|     [[[1], [2], [3]], [[4], [5], [6]]]     | invalid |### 145. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "prefixItems": [
    {},
    {},
    {}
  ],
  "items": false
}

### Results:
| Instance | swift-json-schema (swift) |
|:------------:|:-------:|
|      []      |  valid  |
|     [1]      |  valid  |
|    [1, 2]    |  valid  |
|  [1, 2, 3]   |  valid  |
| [1, 2, 3, 4] | invalid |### 146. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "allOf": [
    {
      "prefixItems": [
        {
          "minimum": 3
        }
      ]
    }
  ],
  "items": {
    "minimum": 5
  }
}

### Results:
| Instance | swift-json-schema (swift) |
|:------:|:-------:|
| [3, 5] | invalid |
| [5, 5] |  valid  |### 147. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "prefixItems": [
    {
      "type": "string"
    }
  ],
  "items": {
    "type": "integer"
  }
}

### Results:
| Instance | swift-json-schema (swift) |
|:-----------:|:-------:|
| ["x", 2, 3] |  valid  |
|  ["x", "y"] | invalid |### 148. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "prefixItems": [
    {}
  ],
  "items": false
}

### Results:
| Instance | swift-json-schema (swift) |
|:------------------:|:-------:|
| ["foo", "bar", 37] | invalid |
|              |  valid  |### 149. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "items": {
    "type": "null"
  }
}

### Results:
| Instance | swift-json-schema (swift) |
|:------:|:-----:|
|  | valid |### 150. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "maxContains": 1
}

### Results:
| Instance | swift-json-schema (swift) |
|:------:|:-----:|
|  [1]   | valid |
| [1, 2] | valid |### 151. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "contains": {
    "const": 1
  },
  "maxContains": 1
}

### Results:
| Instance | swift-json-schema (swift) |
|:---------:|:-------:|
|     []    | invalid |
|    [1]    |  valid  |
|   [1, 1]  | invalid |
|   [1, 2]  |  valid  |
| [1, 2, 1] | invalid |### 152. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "contains": {
    "const": 1
  },
  "maxContains": 1.0
}

### Results:
| Instance | swift-json-schema (swift) |
|:------:|:-------:|
|  [1]   |  valid  |
| [1, 1] | invalid |### 153. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "contains": {
    "const": 1
  },
  "minContains": 1,
  "maxContains": 3
}

### Results:
| Instance | swift-json-schema (swift) |
|:------------:|:-------:|
|      []      | invalid |
|    [1, 1]    |  valid  |
| [1, 1, 1, 1] | invalid |### 154. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "maxItems": 2
}

### Results:
| Instance | swift-json-schema (swift) |
|:---------:|:-------:|
|    [1]    |  valid  |
|   [1, 2]  |  valid  |
| [1, 2, 3] | invalid |
|  "foobar" |  valid  |### 155. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "maxItems": 2.0
}

### Results:
| Instance | swift-json-schema (swift) |
|:---------:|:-------:|
|    [1]    |  valid  |
| [1, 2, 3] | invalid |### 156. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "maxLength": 2
}

### Results:
| Instance | swift-json-schema (swift) |
|:--------------------------:|:-------:|
|            "f"             |  valid  |
|            "fo"            |  valid  |
|           "foo"            | invalid |
|            100             |  valid  |
| "\ud83d\udca9\ud83d\udca9" |  valid  |### 157. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "maxLength": 2.0
}

### Results:
| Instance | swift-json-schema (swift) |
|:-----:|:-------:|
|  "f"  |  valid  |
| "foo" | invalid |### 158. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "maxProperties": 2
}

### Results:
| Instance | swift-json-schema (swift) |
|:------------------------------:|:-------:|
|           {"foo": 1}           |  valid  |
|      {"foo": 1, "bar": 2}      |  valid  |
| {"foo": 1, "bar": 2, "baz": 3} | invalid |
|           [1, 2, 3]            |  valid  |
|            "foobar"            |  valid  |
|               12               |  valid  |### 159. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "maxProperties": 2.0
}

### Results:
| Instance | swift-json-schema (swift) |
|:------------------------------:|:-------:|
|           {"foo": 1}           |  valid  |
| {"foo": 1, "bar": 2, "baz": 3} | invalid |### 160. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "maxProperties": 0
}

### Results:
| Instance | swift-json-schema (swift) |
|:----------:|:-------:|
|     {}     |  valid  |
| {"foo": 1} | invalid |### 161. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "maximum": 3.0
}

### Results:
| Instance | swift-json-schema (swift) |
|:---:|:-------:|
| 2.6 |  valid  |
| 3.0 |  valid  |
| 3.5 | invalid |
| "x" |  valid  |### 162. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "maximum": 300
}

### Results:
| Instance | swift-json-schema (swift) |
|:------:|:-------:|
| 299.97 |  valid  |
|  300   |  valid  |
| 300.0  |  valid  |
| 300.5  | invalid |### 163. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "minContains": 1
}

### Results:
| Instance | swift-json-schema (swift) |
|:---:|:-----:|
| [1] | valid |
|  [] | valid |### 164. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "contains": {
    "const": 1
  },
  "minContains": 1
}

### Results:
| Instance | swift-json-schema (swift) |
|:------:|:-------:|
|   []   | invalid |
|  [2]   | invalid |
|  [1]   |  valid  |
| [1, 2] |  valid  |
| [1, 1] |  valid  |### 165. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "contains": {
    "const": 1
  },
  "minContains": 2
}

### Results:
| Instance | swift-json-schema (swift) |
|:---------:|:-------:|
|     []    | invalid |
|    [1]    | invalid |
|   [1, 2]  | invalid |
|   [1, 1]  |  valid  |
| [1, 1, 1] |  valid  |
| [1, 2, 1] |  valid  |### 166. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "contains": {
    "const": 1
  },
  "minContains": 2.0
}

### Results:
| Instance | swift-json-schema (swift) |
|:------:|:-------:|
|  [1]   | invalid |
| [1, 1] |  valid  |### 167. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "contains": {
    "const": 1
  },
  "maxContains": 2,
  "minContains": 2
}

### Results:
| Instance | swift-json-schema (swift) |
|:---------:|:-------:|
|     []    | invalid |
|    [1]    | invalid |
| [1, 1, 1] | invalid |
|   [1, 1]  |  valid  |### 168. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "contains": {
    "const": 1
  },
  "maxContains": 1,
  "minContains": 3
}

### Results:
| Instance | swift-json-schema (swift) |
|:---------:|:-------:|
|     []    | invalid |
|    [1]    | invalid |
| [1, 1, 1] | invalid |
|   [1, 1]  | invalid |### 169. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "contains": {
    "const": 1
  },
  "minContains": 0
}

### Results:
| Instance | swift-json-schema (swift) |
|:---:|:-----:|
|  [] | valid |
| [2] | valid |### 170. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "contains": {
    "const": 1
  },
  "minContains": 0,
  "maxContains": 1
}

### Results:
| Instance | swift-json-schema (swift) |
|:------:|:-------:|
|   []   |  valid  |
|  [1]   |  valid  |
| [1, 1] | invalid |### 171. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "minItems": 1
}

### Results:
| Instance | swift-json-schema (swift) |
|:------:|:-------:|
| [1, 2] |  valid  |
|  [1]   |  valid  |
|   []   | invalid |
|   ""   |  valid  |### 172. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "minItems": 1.0
}

### Results:
| Instance | swift-json-schema (swift) |
|:------:|:-------:|
| [1, 2] |  valid  |
|   []   | invalid |### 173. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "minLength": 2
}

### Results:
| Instance | swift-json-schema (swift) |
|:--------------:|:-------:|
|     "foo"      |  valid  |
|      "fo"      |  valid  |
|      "f"       | invalid |
|       1        |  valid  |
| "\ud83d\udca9" | invalid |### 174. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "minLength": 2.0
}

### Results:
| Instance | swift-json-schema (swift) |
|:-----:|:-------:|
| "foo" |  valid  |
|  "f"  | invalid |### 175. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "minProperties": 1
}

### Results:
| Instance | swift-json-schema (swift) |
|:--------------------:|:-------:|
| {"foo": 1, "bar": 2} |  valid  |
|      {"foo": 1}      |  valid  |
|          {}          | invalid |
|          []          |  valid  |
|          ""          |  valid  |
|          12          |  valid  |### 176. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "minProperties": 1.0
}

### Results:
| Instance | swift-json-schema (swift) |
|:--------------------:|:-------:|
| {"foo": 1, "bar": 2} |  valid  |
|          {}          | invalid |### 177. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "minimum": 1.1
}

### Results:
| Instance | swift-json-schema (swift) |
|:---:|:-------:|
| 2.6 |  valid  |
| 1.1 |  valid  |
| 0.6 | invalid |
| "x" |  valid  |### 178. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "minimum": -2
}

### Results:
| Instance | swift-json-schema (swift) |
|:-------:|:-------:|
|    -1   |  valid  |
|    0    |  valid  |
|    -2   |  valid  |
|   -2.0  |  valid  |
| -2.0001 | invalid |
|    -3   | invalid |
|   "x"   |  valid  |### 179. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "multipleOf": 2
}

### Results:
| Instance | swift-json-schema (swift) |
|:-----:|:-------:|
|   10  |  valid  |
|   7   | invalid |
| "foo" |  valid  |### 180. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "multipleOf": 1.5
}

### Results:
| Instance | swift-json-schema (swift) |
|:---:|:-------:|
|  0  |  valid  |
| 4.5 |  valid  |
|  35 | invalid |### 181. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "multipleOf": 0.0001
}

### Results:
| Instance | swift-json-schema (swift) |
|:-------:|:-------:|
|  0.0075 |  valid  |
| 0.00751 | invalid |### 182. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "integer",
  "multipleOf": 0.123456789
}

### Results:
| Instance | swift-json-schema (swift) |
|:------:|:-------:|
| 1e+308 | invalid |### 183. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "integer",
  "multipleOf": 1e-08
}

### Results:
| Instance | swift-json-schema (swift) |
|:-----------:|:-----:|
| 12391239123 | valid |### 184. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "not": {
    "type": "integer"
  }
}

### Results:
| Instance | swift-json-schema (swift) |
|:-----:|:-------:|
| "foo" |  valid  |
|   1   | invalid |### 185. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "not": {
    "type": [
      "integer",
      "boolean"
    ]
  }
}

### Results:
| Instance | swift-json-schema (swift) |
|:-----:|:-------:|
| "foo" |  valid  |
|   1   | invalid |
|  true | invalid |### 186. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "not": {
    "type": "object",
    "properties": {
      "foo": {
        "type": "string"
      }
    }
  }
}

### Results:
| Instance | swift-json-schema (swift) |
|:--------------:|:-------:|
|       1        |  valid  |
|   {"foo": 1}   |  valid  |
| {"foo": "bar"} | invalid |### 187. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "properties": {
    "foo": {
      "not": {}
    }
  }
}

### Results:
| Instance | swift-json-schema (swift) |
|:--------------------:|:-------:|
| {"foo": 1, "bar": 2} | invalid |
| {"bar": 1, "baz": 2} |  valid  |### 188. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "not": {}
}

### Results:
| Instance | swift-json-schema (swift) |
|:--------------:|:-------:|
|       1        | invalid |
|     "foo"      | invalid |
|      true      | invalid |
|     false      | invalid |
|      null      | invalid |
| {"foo": "bar"} | invalid |
|       {}       | invalid |
|    ["foo"]     | invalid |
|       []       | invalid |### 189. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "not": true
}

### Results:
| Instance | swift-json-schema (swift) |
|:--------------:|:-------:|
|       1        | invalid |
|     "foo"      | invalid |
|      true      | invalid |
|     false      | invalid |
|      null      | invalid |
| {"foo": "bar"} | invalid |
|       {}       | invalid |
|    ["foo"]     | invalid |
|       []       | invalid |### 190. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "not": false
}

### Results:
| Instance | swift-json-schema (swift) |
|:--------------:|:-----:|
|       1        | valid |
|     "foo"      | valid |
|      true      | valid |
|     false      | valid |
|      null      | valid |
| {"foo": "bar"} | valid |
|       {}       | valid |
|    ["foo"]     | valid |
|       []       | valid |### 191. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "not": {
    "not": {}
  }
}

### Results:
| Instance | swift-json-schema (swift) |
|:-----:|:-----:|
| "foo" | valid |### 192. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "not": {
    "$comment": "this subschema must still produce annotations internally, even though the 'not' will ultimately discard them",
    "anyOf": [
      true,
      {
        "properties": {
          "foo": true
        }
      }
    ],
    "unevaluatedProperties": false
  }
}

### Results:
| Instance | swift-json-schema (swift) |
|:----------:|:-------:|
| {"bar": 1} |  valid  |
| {"foo": 1} | invalid |### 193. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "oneOf": [
    {
      "type": "integer"
    },
    {
      "minimum": 2
    }
  ]
}

### Results:
| Instance | swift-json-schema (swift) |
|:---:|:-------:|
|  1  |  valid  |
| 2.5 |  valid  |
|  3  | invalid |
| 1.5 | invalid |### 194. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "string",
  "oneOf": [
    {
      "minLength": 2
    },
    {
      "maxLength": 4
    }
  ]
}

### Results:
| Instance | swift-json-schema (swift) |
|:--------:|:-------:|
|    3     | invalid |
| "foobar" |  valid  |
|  "foo"   | invalid |### 195. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "oneOf": [
    true,
    true,
    true
  ]
}

### Results:
| Instance | swift-json-schema (swift) |
|:-----:|:-------:|
| "foo" | invalid |### 196. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "oneOf": [
    true,
    false,
    false
  ]
}

### Results:
| Instance | swift-json-schema (swift) |
|:-----:|:-----:|
| "foo" | valid |### 197. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "oneOf": [
    true,
    true,
    false
  ]
}

### Results:
| Instance | swift-json-schema (swift) |
|:-----:|:-------:|
| "foo" | invalid |### 198. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "oneOf": [
    false,
    false,
    false
  ]
}

### Results:
| Instance | swift-json-schema (swift) |
|:-----:|:-------:|
| "foo" | invalid |### 199. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "oneOf": [
    {
      "properties": {
        "bar": {
          "type": "integer"
        }
      },
      "required": [
        "bar"
      ]
    },
    {
      "properties": {
        "foo": {
          "type": "string"
        }
      },
      "required": [
        "foo"
      ]
    }
  ]
}

### Results:
| Instance | swift-json-schema (swift) |
|:-------------------------:|:-------:|
|         {"bar": 2}        |  valid  |
|       {"foo": "baz"}      |  valid  |
|  {"foo": "baz", "bar": 2} | invalid |
| {"foo": 2, "bar": "quux"} | invalid |### 200. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "oneOf": [
    {
      "type": "number"
    },
    {}
  ]
}

### Results:
| Instance | swift-json-schema (swift) |
|:-----:|:-------:|
| "foo" |  valid  |
|  123  | invalid |### 201. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "oneOf": [
    {
      "required": [
        "foo",
        "bar"
      ]
    },
    {
      "required": [
        "foo",
        "baz"
      ]
    }
  ]
}

### Results:
| Instance | swift-json-schema (swift) |
|:------------------------------:|:-------:|
|           {"bar": 2}           | invalid |
|      {"foo": 1, "bar": 2}      |  valid  |
|      {"foo": 1, "baz": 3}      |  valid  |
| {"foo": 1, "bar": 2, "baz": 3} | invalid |### 202. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "oneOf": [
    {
      "properties": {
        "bar": true,
        "baz": true
      },
      "required": [
        "bar"
      ]
    },
    {
      "properties": {
        "foo": true
      },
      "required": [
        "foo"
      ]
    }
  ]
}

### Results:
| Instance | swift-json-schema (swift) |
|:------------------------:|:-------:|
|        {"bar": 8}        |  valid  |
|      {"foo": "foo"}      |  valid  |
| {"foo": "foo", "bar": 8} | invalid |
|     {"baz": "quux"}      | invalid |### 203. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "oneOf": [
    {
      "oneOf": [
        {
          "type": "null"
        }
      ]
    }
  ]
}

### Results:
| Instance | swift-json-schema (swift) |
|:----:|:-------:|
| null |  valid  |
| 123  | invalid |### 204. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "pattern": "^a*$"
}

### Results:
| Instance | swift-json-schema (swift) |
|:-----:|:-------:|
| "aaa" |  valid  |
| "abc" | invalid |
|  true |  valid  |
|  123  |  valid  |
|  1.0  |  valid  |
|   {}  |  valid  |
|   []  |  valid  |
|  null |  valid  |### 205. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "pattern": "a+"
}

### Results:
| Instance | swift-json-schema (swift) |
|:--------:|:-----:|
| "xxaayy" | valid |### 206. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "patternProperties": {
    "f.*o": {
      "type": "integer"
    }
  }
}

### Results:
| Instance | swift-json-schema (swift) |
|:--------------------------------:|:-------:|
|            {"foo": 1}            |  valid  |
|     {"foo": 1, "foooooo": 2}     |  valid  |
|   {"foo": "bar", "fooooo": 2}    | invalid |
| {"foo": "bar", "foooooo": "baz"} | invalid |
|             ["foo"]              |  valid  |
|              "foo"               |  valid  |
|                12                |  valid  |### 207. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "patternProperties": {
    "a*": {
      "type": "integer"
    },
    "aaa*": {
      "maximum": 20
    }
  }
}

### Results:
| Instance | swift-json-schema (swift) |
|:--------------------------:|:-------:|
|         {"a": 21}          |  valid  |
|        {"aaaa": 18}        |  valid  |
|   {"a": 21, "aaaa": 18}    |  valid  |
|        {"a": "bar"}        | invalid |
|        {"aaaa": 31}        | invalid |
| {"aaa": "foo", "aaaa": 31} | invalid |### 208. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "patternProperties": {
    "[0-9]{2,}": {
      "type": "boolean"
    },
    "X_": {
      "type": "string"
    }
  }
}

### Results:
| Instance | swift-json-schema (swift) |
|:------------------:|:-------:|
| {"answer 1": "42"} |  valid  |
|   {"a31b": null}   | invalid |
|    {"a_x_3": 3}    |  valid  |
|    {"a_X_3": 3}    | invalid |### 209. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "patternProperties": {
    "f.*": true,
    "b.*": false
  }
}

### Results:
| Instance | swift-json-schema (swift) |
|:--------------------:|:-------:|
|      {"foo": 1}      |  valid  |
|      {"bar": 2}      | invalid |
| {"foo": 1, "bar": 2} | invalid |
|    {"foobar": 1}     | invalid |
|          {}          |  valid  |### 210. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "patternProperties": {
    "^.*bar$": {
      "type": "null"
    }
  }
}

### Results:
| Instance | swift-json-schema (swift) |
|:----------------:|:-----:|
| {"foobar": null} | valid |### 211. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "prefixItems": [
    {
      "type": "integer"
    },
    {
      "type": "string"
    }
  ]
}

### Results:
| Instance | swift-json-schema (swift) |
|:-------------------------------------------:|:-------:|
|                  [1, "foo"]                 |  valid  |
|                  ["foo", 1]                 | invalid |
|                     [1]                     |  valid  |
|               [1, "foo", true]              |  valid  |
|                      []                     |  valid  |
| {"0": "invalid", "1": "valid", "length": 2} |  valid  |### 212. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "prefixItems": [
    true,
    false
  ]
}

### Results:
| Instance | swift-json-schema (swift) |
|:----------:|:-------:|
|    [1]     |  valid  |
| [1, "foo"] | invalid |
|     []     |  valid  |### 213. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "prefixItems": [
    {
      "type": "integer"
    }
  ]
}

### Results:
| Instance | swift-json-schema (swift) |
|:-----------------:|:-----:|
| [1, "foo", false] | valid |### 214. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "prefixItems": [
    {
      "type": "null"
    }
  ]
}

### Results:
| Instance | swift-json-schema (swift) |
|:------:|:-----:|
|  | valid |### 215. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "properties": {
    "foo": {
      "type": "integer"
    },
    "bar": {
      "type": "string"
    }
  }
}

### Results:
| Instance | swift-json-schema (swift) |
|:------------------------:|:-------:|
| {"foo": 1, "bar": "baz"} |  valid  |
|  {"foo": 1, "bar": {}}   | invalid |
|  {"foo": [], "bar": {}}  | invalid |
|       {"quux": []}       |  valid  |
|            []            |  valid  |
|            12            |  valid  |### 216. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "properties": {
    "foo": {
      "type": "array",
      "maxItems": 3
    },
    "bar": {
      "type": "array"
    }
  },
  "patternProperties": {
    "f.o": {
      "minItems": 2
    }
  },
  "additionalProperties": {
    "type": "integer"
  }
}

### Results:
| Instance | swift-json-schema (swift) |
|:---------------------:|:-------:|
|    {"foo": [1, 2]}    |  valid  |
| {"foo": [1, 2, 3, 4]} | invalid |
|      {"foo": []}      | invalid |
|    {"fxo": [1, 2]}    |  valid  |
|      {"fxo": []}      | invalid |
|      {"bar": []}      |  valid  |
|      {"quux": 3}      |  valid  |
|    {"quux": "foo"}    | invalid |### 217. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "properties": {
    "foo": true,
    "bar": false
  }
}

### Results:
| Instance | swift-json-schema (swift) |
|:--------------------:|:-------:|
|          {}          |  valid  |
|      {"foo": 1}      |  valid  |
|      {"bar": 2}      | invalid |
| {"foo": 1, "bar": 2} | invalid |### 218. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "properties": {
    "foo\nbar": {
      "type": "number"
    },
    "foo\"bar": {
      "type": "number"
    },
    "foo\\bar": {
      "type": "number"
    },
    "foo\rbar": {
      "type": "number"
    },
    "foo\tbar": {
      "type": "number"
    },
    "foo\fbar": {
      "type": "number"
    }
  }
}

### Results:
| Instance | swift-json-schema (swift) |
|:------------------------------------------------------------------------------------------------------:|:-------:|
|       {"foo\nbar": 1, "foo\"bar": 1, "foo\\bar": 1, "foo\rbar": 1, "foo\tbar": 1, "foo\fbar": 1}       |  valid  |
| {"foo\nbar": "1", "foo\"bar": "1", "foo\\bar": "1", "foo\rbar": "1", "foo\tbar": "1", "foo\fbar": "1"} | invalid |### 219. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "properties": {
    "foo": {
      "type": "null"
    }
  }
}

### Results:
| Instance | swift-json-schema (swift) |
|:-------------:|:-----:|
| {"foo": null} | valid |### 220. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "properties": {
    "__proto__": {
      "type": "number"
    },
    "toString": {
      "properties": {
        "length": {
          "type": "string"
        }
      }
    },
    "constructor": {
      "type": "number"
    }
  }
}

### Results:
| Instance | swift-json-schema (swift) |
|:-------------------------------------------------------------------:|:-------:|
|                                  []                                 |  valid  |
|                                  12                                 |  valid  |
|                                  {}                                 |  valid  |
|                         {"__proto__": "foo"}                        | invalid |
|                     {"toString": {"length": 37}}                    | invalid |
|                   {"constructor": {"length": 37}}                   | invalid |
| {"__proto__": 12, "toString": {"length": "foo"}, "constructor": 37} |  valid  |### 221. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "propertyNames": {
    "maxLength": 3
  }
}

### Results:
| Instance | swift-json-schema (swift) |
|:-------------------------:|:-------:|
|    {"f": {}, "foo": {}}   |  valid  |
| {"foo": {}, "foobar": {}} | invalid |
|             {}            |  valid  |
|        [1, 2, 3, 4]       |  valid  |
|          "foobar"         |  valid  |
|             12            |  valid  |### 222. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "propertyNames": {
    "pattern": "^a+$"
  }
}

### Results:
| Instance | swift-json-schema (swift) |
|:------------------------------:|:-------:|
| {"a": {}, "aa": {}, "aaa": {}} |  valid  |
|          {"aaA": {}}           | invalid |
|               {}               |  valid  |### 223. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "propertyNames": true
}

### Results:
| Instance | swift-json-schema (swift) |
|:----------:|:-----:|
| {"foo": 1} | valid |
|     {}     | valid |### 224. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "propertyNames": false
}

### Results:
| Instance | swift-json-schema (swift) |
|:----------:|:-------:|
| {"foo": 1} | invalid |
|     {}     |  valid  |### 225. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "propertyNames": {
    "const": "foo"
  }
}

### Results:
| Instance | swift-json-schema (swift) |
|:----------:|:-------:|
| {"foo": 1} |  valid  |
| {"bar": 1} | invalid |
|     {}     |  valid  |### 226. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "propertyNames": {
    "enum": [
      "foo",
      "bar"
    ]
  }
}

### Results:
| Instance | swift-json-schema (swift) |
|:--------------------:|:-------:|
|      {"foo": 1}      |  valid  |
| {"foo": 1, "bar": 1} |  valid  |
|      {"baz": 1}      | invalid |
|          {}          |  valid  |### 227. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "properties": {
    "foo": {
      "$ref": "#"
    }
  },
  "additionalProperties": false
}

### Results:
| Instance | swift-json-schema (swift) |
|:-----------------------:|:-------:|
|      {"foo": false}     |  valid  |
| {"foo": {"foo": false}} |  valid  |
|      {"bar": false}     | invalid |
| {"foo": {"bar": false}} | invalid |### 228. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "properties": {
    "foo": {
      "type": "integer"
    },
    "bar": {
      "$ref": "#/properties/foo"
    }
  }
}

### Results:
| Instance | swift-json-schema (swift) |
|:-------------:|:-------:|
|   {"bar": 3}  |  valid  |
| {"bar": true} | invalid |### 229. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "prefixItems": [
    {
      "type": "integer"
    },
    {
      "$ref": "#/prefixItems/0"
    }
  ]
}

### Results:
| Instance | swift-json-schema (swift) |
|:----------:|:-------:|
|   [1, 2]   |  valid  |
| [1, "foo"] | invalid |### 230. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$defs": {
    "tilde~field": {
      "type": "integer"
    },
    "slash/field": {
      "type": "integer"
    },
    "percent%field": {
      "type": "integer"
    }
  },
  "properties": {
    "tilde": {
      "$ref": "#/$defs/tilde~0field"
    },
    "slash": {
      "$ref": "#/$defs/slash~1field"
    },
    "percent": {
      "$ref": "#/$defs/percent%25field"
    }
  }
}

### Results:
| Instance | swift-json-schema (swift) |
|:-------------------:|:-------:|
|  {"slash": "aoeu"}  | invalid |
|  {"tilde": "aoeu"}  | invalid |
| {"percent": "aoeu"} | invalid |
|    {"slash": 123}   |  valid  |
|    {"tilde": 123}   |  valid  |
|   {"percent": 123}  |  valid  |### 231. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$defs": {
    "a": {
      "type": "integer"
    },
    "b": {
      "$ref": "#/$defs/a"
    },
    "c": {
      "$ref": "#/$defs/b"
    }
  },
  "$ref": "#/$defs/c"
}

### Results:
| Instance | swift-json-schema (swift) |
|:---:|:-------:|
|  5  |  valid  |
| "a" | invalid |### 232. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$defs": {
    "reffed": {
      "type": "array"
    }
  },
  "properties": {
    "foo": {
      "$ref": "#/$defs/reffed",
      "maxItems": 2
    }
  }
}

### Results:
| Instance | swift-json-schema (swift) |
|:------------------:|:-------:|
|    {"foo": []}     |  valid  |
| {"foo": [1, 2, 3]} | invalid |
| {"foo": "string"}  | invalid |### 233. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$ref": "https://json-schema.org/draft/2020-12/schema"
}

### Results:
| Instance | swift-json-schema (swift) |
|:-----------------:|:-----:|
|  {"minLength": 1} | error |
| {"minLength": -1} | error |### 234. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "properties": {
    "$ref": {
      "type": "string"
    }
  }
}

### Results:
| Instance | swift-json-schema (swift) |
|:-------------:|:-------:|
| {"$ref": "a"} |  valid  |
|  {"$ref": 2}  | invalid |### 235. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "properties": {
    "$ref": {
      "$ref": "#/$defs/is-string"
    }
  },
  "$defs": {
    "is-string": {
      "type": "string"
    }
  }
}

### Results:
| Instance | swift-json-schema (swift) |
|:-------------:|:-------:|
| {"$ref": "a"} |  valid  |
|  {"$ref": 2}  | invalid |### 236. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$ref": "#/$defs/bool",
  "$defs": {
    "bool": true
  }
}

### Results:
| Instance | swift-json-schema (swift) |
|:-----:|:-----:|
| "foo" | valid |### 237. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$ref": "#/$defs/bool",
  "$defs": {
    "bool": false
  }
}

### Results:
| Instance | swift-json-schema (swift) |
|:-----:|:-------:|
| "foo" | invalid |### 238. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "http://localhost:1234/draft2020-12/tree",
  "description": "tree of nodes",
  "type": "object",
  "properties": {
    "meta": {
      "type": "string"
    },
    "nodes": {
      "type": "array",
      "items": {
        "$ref": "node"
      }
    }
  },
  "required": [
    "meta",
    "nodes"
  ],
  "$defs": {
    "node": {
      "$id": "http://localhost:1234/draft2020-12/node",
      "description": "node",
      "type": "object",
      "properties": {
        "value": {
          "type": "number"
        },
        "subtree": {
          "$ref": "tree"
        }
      },
      "required": [
        "value"
      ]
    }
  }
}

### Results:
| Instance | swift-json-schema (swift) |
|:------------------------------------------------------------------------------------------------------------------------------------------------------------------
-------------------------------------------------------:|:-------:|
|         {"meta": "root", "nodes": [{"value": 1, "subtree": {"meta": "child", "nodes": [{"value": 1.1}, {"value": 1.2}]}}, {"value": 2, "subtree": {"meta": 
"child", "nodes": [{"value": 2.1}, {"value": 2.2}]}}]}         |  valid  |
| {"meta": "root", "nodes": [{"value": 1, "subtree": {"meta": "child", "nodes": [{"value": "string is invalid"}, {"value": 1.2}]}}, {"value": 2, "subtree": {"meta":
"child", "nodes": [{"value": 2.1}, {"value": 2.2}]}}]} | invalid |### 239. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "properties": {
    "foo\"bar": {
      "$ref": "#/$defs/foo%22bar"
    }
  },
  "$defs": {
    "foo\"bar": {
      "type": "number"
    }
  }
}

### Results:
| Instance | swift-json-schema (swift) |
|:-----------------:|:-------:|
|  {"foo\"bar": 1}  |  valid  |
| {"foo\"bar": "1"} | invalid |### 240. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$defs": {
    "A": {
      "unevaluatedProperties": false
    }
  },
  "properties": {
    "prop1": {
      "type": "string"
    }
  },
  "$ref": "#/$defs/A"
}

### Results:
| Instance | swift-json-schema (swift) |
|:------------------:|:-------:|
| {"prop1": "match"} | invalid |### 241. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$defs": {
    "a_string": {
      "type": "string"
    }
  },
  "enum": [
    {
      "$ref": "#/$defs/a_string"
    }
  ]
}

### Results:
| Instance | swift-json-schema (swift) |
|:----------------------------:|:-------:|
|      "this is a string"      | invalid |
|      {"type": "string"}      | invalid |
| {"$ref": "#/$defs/a_string"} |  valid  |### 242. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "http://example.com/schema-relative-uri-defs1.json",
  "properties": {
    "foo": {
      "$id": "schema-relative-uri-defs2.json",
      "$defs": {
        "inner": {
          "properties": {
            "bar": {
              "type": "string"
            }
          }
        }
      },
      "$ref": "#/$defs/inner"
    }
  },
  "$ref": "schema-relative-uri-defs2.json"
}

### Results:
| Instance | swift-json-schema (swift) |
|:---------------------------------:|:-------:|
|  {"foo": {"bar": 1}, "bar": "a"}  | invalid |
|  {"foo": {"bar": "a"}, "bar": 1}  | invalid |
| {"foo": {"bar": "a"}, "bar": "a"} |  valid  |### 243. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "http://example.com/schema-refs-absolute-uris-defs1.json",
  "properties": {
    "foo": {
      "$id": "http://example.com/schema-refs-absolute-uris-defs2.json",
      "$defs": {
        "inner": {
          "properties": {
            "bar": {
              "type": "string"
            }
          }
        }
      },
      "$ref": "#/$defs/inner"
    }
  },
  "$ref": "schema-refs-absolute-uris-defs2.json"
}

### Results:
| Instance | swift-json-schema (swift) |
|:---------------------------------:|:-------:|
|  {"foo": {"bar": 1}, "bar": "a"}  | invalid |
|  {"foo": {"bar": "a"}, "bar": 1}  | invalid |
| {"foo": {"bar": "a"}, "bar": "a"} |  valid  |### 244. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "http://example.com/a.json",
  "$defs": {
    "x": {
      "$id": "http://example.com/b/c.json",
      "not": {
        "$defs": {
          "y": {
            "$id": "d.json",
            "type": "number"
          }
        }
      }
    }
  },
  "allOf": [
    {
      "$ref": "http://example.com/b/d.json"
    }
  ]
}

### Results:
| Instance | swift-json-schema (swift) |
|:---:|:-------:|
|  1  |  valid  |
| "a" | invalid |### 245. Schema:
 {
  "$comment": "$id must be evaluated before $ref to get the proper $ref destination",
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://example.com/draft2020-12/ref-and-id1/base.json",
  "$ref": "int.json",
  "$defs": {
    "bigint": {
      "$comment": "canonical uri: https://example.com/ref-and-id1/int.json",
      "$id": "int.json",
      "maximum": 10
    },
    "smallint": {
      "$comment": "canonical uri: https://example.com/ref-and-id1-int.json",
      "$id": "/draft2020-12/ref-and-id1-int.json",
      "maximum": 2
    }
  }
}

### Results:
| Instance | swift-json-schema (swift) |
|:--:|:-------:|
| 5  |  valid  |
| 50 | invalid |### 246. Schema:
 {
  "$comment": "$id must be evaluated before $ref to get the proper $ref destination",
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://example.com/draft2020-12/ref-and-id2/base.json",
  "$ref": "#bigint",
  "$defs": {
    "bigint": {
      "$comment": "canonical uri: /ref-and-id2/base.json#/$defs/bigint; another valid uri for this location: /ref-and-id2/base.json#bigint",
      "$anchor": "bigint",
      "maximum": 10
    },
    "smallint": {
      "$comment": "canonical uri: https://example.com/ref-and-id2#/$defs/smallint; another valid uri for this location: https://example.com/ref-and-id2/#bigint",
      "$id": "https://example.com/draft2020-12/ref-and-id2/",
      "$anchor": "bigint",
      "maximum": 2
    }
  }
}

### Results:
| Instance | swift-json-schema (swift) |
|:--:|:-------:|
| 5  |  valid  |
| 50 | invalid |### 247. Schema:
 {
  "$comment": "URIs do not have to have HTTP(s) schemes",
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:uuid:deadbeef-1234-ffff-ffff-4321feebdaed",
  "minimum": 30,
  "properties": {
    "foo": {
      "$ref": "urn:uuid:deadbeef-1234-ffff-ffff-4321feebdaed"
    }
  }
}

### Results:
| Instance | swift-json-schema (swift) |
|:-----------:|:-------:|
| {"foo": 37} |  valid  |
| {"foo": 12} | invalid |### 248. Schema:
 {
  "$comment": "URIs do not have to have HTTP(s) schemes",
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:uuid:deadbeef-1234-00ff-ff00-4321feebdaed",
  "properties": {
    "foo": {
      "$ref": "#/$defs/bar"
    }
  },
  "$defs": {
    "bar": {
      "type": "string"
    }
  }
}

### Results:
| Instance | swift-json-schema (swift) |
|:--------------:|:-------:|
| {"foo": "bar"} |  valid  |
|  {"foo": 12}   | invalid |### 249. Schema:
 {
  "$comment": "RFC 8141 \u00a72.2",
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:example:1/406/47452/2",
  "properties": {
    "foo": {
      "$ref": "#/$defs/bar"
    }
  },
  "$defs": {
    "bar": {
      "type": "string"
    }
  }
}

### Results:
| Instance | swift-json-schema (swift) |
|:--------------:|:-------:|
| {"foo": "bar"} |  valid  |
|  {"foo": 12}   | invalid |### 250. Schema:
 {
  "$comment": "RFC 8141 \u00a72.3.1",
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:example:foo-bar-baz-qux?+CCResolve:cc=uk",
  "properties": {
    "foo": {
      "$ref": "#/$defs/bar"
    }
  },
  "$defs": {
    "bar": {
      "type": "string"
    }
  }
}

### Results:
| Instance | swift-json-schema (swift) |
|:--------------:|:-------:|
| {"foo": "bar"} |  valid  |
|  {"foo": 12}   | invalid |### 251. Schema:
 {
  "$comment": "RFC 8141 \u00a72.3.2",
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:example:weather?=op=map&lat=39.56&lon=-104.85&datetime=1969-07-21T02:56:15Z",
  "properties": {
    "foo": {
      "$ref": "#/$defs/bar"
    }
  },
  "$defs": {
    "bar": {
      "type": "string"
    }
  }
}

### Results:
| Instance | swift-json-schema (swift) |
|:--------------:|:-------:|
| {"foo": "bar"} |  valid  |
|  {"foo": 12}   | invalid |### 252. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:uuid:deadbeef-1234-0000-0000-4321feebdaed",
  "properties": {
    "foo": {
      "$ref": "urn:uuid:deadbeef-1234-0000-0000-4321feebdaed#/$defs/bar"
    }
  },
  "$defs": {
    "bar": {
      "type": "string"
    }
  }
}

### Results:
| Instance | swift-json-schema (swift) |
|:--------------:|:-------:|
| {"foo": "bar"} |  valid  |
|  {"foo": 12}   | invalid |### 253. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:uuid:deadbeef-1234-ff00-00ff-4321feebdaed",
  "properties": {
    "foo": {
      "$ref": "urn:uuid:deadbeef-1234-ff00-00ff-4321feebdaed#something"
    }
  },
  "$defs": {
    "bar": {
      "$anchor": "something",
      "type": "string"
    }
  }
}

### Results:
| Instance | swift-json-schema (swift) |
|:--------------:|:-------:|
| {"foo": "bar"} |  valid  |
|  {"foo": 12}   | invalid |### 254. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$ref": "urn:uuid:deadbeef-4321-ffff-ffff-1234feebdaed",
  "$defs": {
    "foo": {
      "$id": "urn:uuid:deadbeef-4321-ffff-ffff-1234feebdaed",
      "$defs": {
        "bar": {
          "type": "string"
        }
      },
      "$ref": "#/$defs/bar"
    }
  }
}

### Results:
| Instance | swift-json-schema (swift) |
|:-----:|:-------:|
| "bar" |  valid  |
|   12  | invalid |### 255. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$ref": "http://example.com/ref/if",
  "if": {
    "$id": "http://example.com/ref/if",
    "type": "integer"
  }
}

### Results:
| Instance | swift-json-schema (swift) |
|:-----:|:-------:|
| "foo" | invalid |
|   12  |  valid  |### 256. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$ref": "http://example.com/ref/then",
  "then": {
    "$id": "http://example.com/ref/then",
    "type": "integer"
  }
}

### Results:
| Instance | swift-json-schema (swift) |
|:-----:|:-------:|
| "foo" | invalid |
|   12  |  valid  |### 257. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$ref": "http://example.com/ref/else",
  "else": {
    "$id": "http://example.com/ref/else",
    "type": "integer"
  }
}

### Results:
| Instance | swift-json-schema (swift) |
|:-----:|:-------:|
| "foo" | invalid |
|   12  |  valid  |### 258. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "http://example.com/ref/absref.json",
  "$defs": {
    "a": {
      "$id": "http://example.com/ref/absref/foobar.json",
      "type": "number"
    },
    "b": {
      "$id": "http://example.com/absref/foobar.json",
      "type": "string"
    }
  },
  "$ref": "/absref/foobar.json"
}

### Results:
| Instance | swift-json-schema (swift) |
|:-----:|:-------:|
| "foo" |  valid  |
|   12  | invalid |### 259. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "file:///folder/file.json",
  "$defs": {
    "foo": {
      "type": "number"
    }
  },
  "$ref": "#/$defs/foo"
}

### Results:
| Instance | swift-json-schema (swift) |
|:---:|:-------:|
|  1  |  valid  |
| "a" | invalid |### 260. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "file:///c:/folder/file.json",
  "$defs": {
    "foo": {
      "type": "number"
    }
  },
  "$ref": "#/$defs/foo"
}

### Results:
| Instance | swift-json-schema (swift) |
|:---:|:-------:|
|  1  |  valid  |
| "a" | invalid |### 261. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$defs": {
    "": {
      "$defs": {
        "": {
          "type": "number"
        }
      }
    }
  },
  "allOf": [
    {
      "$ref": "#/$defs//$defs/"
    }
  ]
}

### Results:
| Instance | swift-json-schema (swift) |
|:---:|:-------:|
|  1  |  valid  |
| "a" | invalid |### 262. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$ref": "http://localhost:1234/draft2020-12/integer.json"
}

### Results:
| Instance | swift-json-schema (swift) |
|:---:|:-------:|
|  1  |  valid  |
| "a" | invalid |### 263. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$ref": "http://localhost:1234/draft2020-12/subSchemas.json#/$defs/integer"
}

### Results:
| Instance | swift-json-schema (swift) |
|:---:|:-------:|
|  1  |  valid  |
| "a" | invalid |### 264. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$ref": "http://localhost:1234/draft2020-12/locationIndependentIdentifier.json#foo"
}

### Results:
| Instance | swift-json-schema (swift) |
|:---:|:-------:|
|  1  |  valid  |
| "a" | invalid |### 265. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$ref": "http://localhost:1234/draft2020-12/subSchemas.json#/$defs/refToInteger"
}

### Results:
| Instance | swift-json-schema (swift) |
|:---:|:-------:|
|  1  |  valid  |
| "a" | invalid |### 266. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "http://localhost:1234/draft2020-12/",
  "items": {
    "$id": "baseUriChange/",
    "items": {
      "$ref": "folderInteger.json"
    }
  }
}

### Results:
| Instance | swift-json-schema (swift) |
|:-------:|:-------:|
|  [[1]]  |  valid  |
| [["a"]] | invalid |### 267. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "http://localhost:1234/draft2020-12/scope_change_defs1.json",
  "type": "object",
  "properties": {
    "list": {
      "$ref": "baseUriChangeFolder/"
    }
  },
  "$defs": {
    "baz": {
      "$id": "baseUriChangeFolder/",
      "type": "array",
      "items": {
        "$ref": "folderInteger.json"
      }
    }
  }
}

### Results:
| Instance | swift-json-schema (swift) |
|:---------------:|:-------:|
|  {"list": [1]}  |  valid  |
| {"list": ["a"]} | invalid |### 268. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "http://localhost:1234/draft2020-12/scope_change_defs2.json",
  "type": "object",
  "properties": {
    "list": {
      "$ref": "baseUriChangeFolderInSubschema/#/$defs/bar"
    }
  },
  "$defs": {
    "baz": {
      "$id": "baseUriChangeFolderInSubschema/",
      "$defs": {
        "bar": {
          "type": "array",
          "items": {
            "$ref": "folderInteger.json"
          }
        }
      }
    }
  }
}

### Results:
| Instance | swift-json-schema (swift) |
|:---------------:|:-------:|
|  {"list": [1]}  |  valid  |
| {"list": ["a"]} | invalid |### 269. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "http://localhost:1234/draft2020-12/object",
  "type": "object",
  "properties": {
    "name": {
      "$ref": "name-defs.json#/$defs/orNull"
    }
  }
}

### Results:
| Instance | swift-json-schema (swift) |
|:------------------------:|:-------:|
|     {"name": "foo"}      |  valid  |
|      {"name": null}      |  valid  |
| {"name": {"name": null}} | invalid |### 270. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "http://localhost:1234/draft2020-12/schema-remote-ref-ref-defs1.json",
  "$ref": "ref-and-defs.json"
}

### Results:
| Instance | swift-json-schema (swift) |
|:------------:|:-------:|
|  {"bar": 1}  | invalid |
| {"bar": "a"} |  valid  |### 271. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$ref": "http://localhost:1234/draft2020-12/locationIndependentIdentifier.json#/$defs/refToInteger"
}

### Results:
| Instance | swift-json-schema (swift) |
|:-----:|:-------:|
|   1   |  valid  |
| "foo" | invalid |### 272. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "http://localhost:1234/draft2020-12/some-id",
  "properties": {
    "name": {
      "$ref": "nested/foo-ref-string.json"
    }
  }
}

### Results:
| Instance | swift-json-schema (swift) |
|:----------------------:|:-------:|
|  {"name": {"foo": 1}}  | invalid |
| {"name": {"foo": "a"}} |  valid  |### 273. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$ref": "http://localhost:1234/different-id-ref-string.json"
}

### Results:
| Instance | swift-json-schema (swift) |
|:-----:|:-------:|
|   1   | invalid |
| "foo" |  valid  |### 274. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$ref": "http://localhost:1234/urn-ref-string.json"
}

### Results:
| Instance | swift-json-schema (swift) |
|:-----:|:-------:|
|   1   | invalid |
| "foo" |  valid  |### 275. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$ref": "http://localhost:1234/nested-absolute-ref-to-string.json"
}

### Results:
| Instance | swift-json-schema (swift) |
|:-----:|:-------:|
|   1   | invalid |
| "foo" | invalid |### 276. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$ref": "http://localhost:1234/draft2020-12/detached-ref.json#/$defs/foo"
}

### Results:
| Instance | swift-json-schema (swift) |
|:---:|:-------:|
|  1  |  valid  |
| "a" | invalid |### 277. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "properties": {
    "foo": {},
    "bar": {}
  },
  "required": [
    "foo"
  ]
}

### Results:
| Instance | swift-json-schema (swift) |
|:----------:|:-------:|
| {"foo": 1} |  valid  |
| {"bar": 1} | invalid |
|     []     |  valid  |
|     ""     |  valid  |
|     12     |  valid  |### 278. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "properties": {
    "foo": {}
  }
}

### Results:
| Instance | swift-json-schema (swift) |
|:--:|:-----:|
| {} | valid |### 279. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "properties": {
    "foo": {}
  },
  "required": []
}

### Results:
| Instance | swift-json-schema (swift) |
|:--:|:-----:|
| {} | valid |### 280. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "required": [
    "foo\nbar",
    "foo\"bar",
    "foo\\bar",
    "foo\rbar",
    "foo\tbar",
    "foo\fbar"
  ]
}

### Results:
| Instance | swift-json-schema (swift) |
|:------------------------------------------------------------------------------------------:|:-------:|
| {"foo\nbar": 1, "foo\"bar": 1, "foo\\bar": 1, "foo\rbar": 1, "foo\tbar": 1, "foo\fbar": 1} |  valid  |
|                             {"foo\nbar": "1", "foo\"bar": "1"}                             | invalid |### 281. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "required": [
    "__proto__",
    "toString",
    "constructor"
  ]
}

### Results:
| Instance | swift-json-schema (swift) |
|:-------------------------------------------------------------------:|:-------:|
|                                  []                                 |  valid  |
|                                  12                                 |  valid  |
|                                  {}                                 | invalid |
|                         {"__proto__": "foo"}                        | invalid |
|                     {"toString": {"length": 37}}                    | invalid |
|                   {"constructor": {"length": 37}}                   | invalid |
| {"__proto__": 12, "toString": {"length": "foo"}, "constructor": 37} |  valid  |### 282. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "integer"
}

### Results:
| Instance | swift-json-schema (swift) |
|:-----:|:-------:|
|   1   |  valid  |
|  1.0  |  valid  |
|  1.1  | invalid |
| "foo" | invalid |
|  "1"  | invalid |
|   {}  | invalid |
|   []  | invalid |
|  true | invalid |
|  null | invalid |### 283. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "number"
}

### Results:
| Instance | swift-json-schema (swift) |
|:-----:|:-------:|
|   1   |  valid  |
|  1.0  |  valid  |
|  1.1  |  valid  |
| "foo" | invalid |
|  "1"  | invalid |
|   {}  | invalid |
|   []  | invalid |
|  true | invalid |
|  null | invalid |### 284. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "string"
}

### Results:
| Instance | swift-json-schema (swift) |
|:-----:|:-------:|
|   1   | invalid |
|  1.1  | invalid |
| "foo" |  valid  |
|  "1"  |  valid  |
|   ""  |  valid  |
|   {}  | invalid |
|   []  | invalid |
|  true | invalid |
|  null | invalid |### 285. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object"
}

### Results:
| Instance | swift-json-schema (swift) |
|:-----:|:-------:|
|   1   | invalid |
|  1.1  | invalid |
| "foo" | invalid |
|   {}  |  valid  |
|   []  | invalid |
|  true | invalid |
|  null | invalid |### 286. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "array"
}

### Results:
| Instance | swift-json-schema (swift) |
|:-----:|:-------:|
|   1   | invalid |
|  1.1  | invalid |
| "foo" | invalid |
|   {}  | invalid |
|   []  |  valid  |
|  true | invalid |
|  null | invalid |### 287. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "boolean"
}

### Results:
| Instance | swift-json-schema (swift) |
|:-----:|:-------:|
|   1   | invalid |
|   0   | invalid |
|  1.1  | invalid |
| "foo" | invalid |
|   ""  | invalid |
|   {}  | invalid |
|   []  | invalid |
|  true |  valid  |
| false |  valid  |
|  null | invalid |### 288. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "null"
}

### Results:
| Instance | swift-json-schema (swift) |
|:-----:|:-------:|
|   1   | invalid |
|  1.1  | invalid |
|   0   | invalid |
| "foo" | invalid |
|   ""  | invalid |
|   {}  | invalid |
|   []  | invalid |
|  true | invalid |
| false | invalid |
|  null |  valid  |### 289. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": [
    "integer",
    "string"
  ]
}

### Results:
| Instance | swift-json-schema (swift) |
|:-----:|:-------:|
|   1   |  valid  |
| "foo" |  valid  |
|  1.1  | invalid |
|   {}  | invalid |
|   []  | invalid |
|  true | invalid |
|  null | invalid |### 290. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": [
    "string"
  ]
}

### Results:
| Instance | swift-json-schema (swift) |
|:-----:|:-------:|
| "foo" |  valid  |
|  123  | invalid |### 291. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": [
    "array",
    "object"
  ]
}

### Results:
| Instance | swift-json-schema (swift) |
|:------------:|:-------:|
|  [1, 2, 3]   |  valid  |
| {"foo": 123} |  valid  |
|     123      | invalid |
|    "foo"     | invalid |
|     null     | invalid |### 292. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": [
    "array",
    "object",
    "null"
  ]
}

### Results:
| Instance | swift-json-schema (swift) |
|:------------:|:-------:|
|  [1, 2, 3]   |  valid  |
| {"foo": 123} |  valid  |
|     null     |  valid  |
|     123      | invalid |
|    "foo"     | invalid |### 293. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "unevaluatedItems": true
}

### Results:
| Instance | swift-json-schema (swift) |
|:-------:|:-----:|
|    []   | valid |
| ["foo"] | valid |### 294. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "unevaluatedItems": false
}

### Results:
| Instance | swift-json-schema (swift) |
|:-------:|:-------:|
|    []   |  valid  |
| ["foo"] | invalid |### 295. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "unevaluatedItems": {
    "type": "string"
  }
}

### Results:
| Instance | swift-json-schema (swift) |
|:-------:|:-------:|
|    []   |  valid  |
| ["foo"] |  valid  |
|   [42]  | invalid |### 296. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "items": {
    "type": "string"
  },
  "unevaluatedItems": false
}

### Results:
| Instance | swift-json-schema (swift) |
|:--------------:|:-----:|
| ["foo", "bar"] | valid |### 297. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "prefixItems": [
    {
      "type": "string"
    }
  ],
  "unevaluatedItems": false
}

### Results:
| Instance | swift-json-schema (swift) |
|:--------------:|:-------:|
|    ["foo"]     |  valid  |
| ["foo", "bar"] | invalid |### 298. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "prefixItems": [
    {
      "type": "string"
    }
  ],
  "items": true,
  "unevaluatedItems": false
}

### Results:
| Instance | swift-json-schema (swift) |
|:-----------:|:-----:|
| ["foo", 42] | valid |### 299. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "items": {
    "type": "number"
  },
  "unevaluatedItems": {
    "type": "string"
  }
}

### Results:
| Instance | swift-json-schema (swift) |
|:---------------------:|:-------:|
|      [5, 6, 7, 8]     |  valid  |
| ["foo", "bar", "baz"] | invalid |### 300. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "prefixItems": [
    {
      "type": "string"
    }
  ],
  "allOf": [
    {
      "prefixItems": [
        true,
        {
          "type": "number"
        }
      ]
    }
  ],
  "unevaluatedItems": false
}

### Results:
| Instance | swift-json-schema (swift) |
|:-----------------:|:-------:|
|    ["foo", 42]    |  valid  |
| ["foo", 42, true] | invalid |### 301. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "unevaluatedItems": {
    "type": "boolean"
  },
  "anyOf": [
    {
      "items": {
        "type": "string"
      }
    },
    true
  ]
}

### Results:
| Instance | swift-json-schema (swift) |
|:--------------:|:-------:|
|   |  valid  |
| ["yes", "no"]  |  valid  |
| ["yes", false] | invalid |### 302. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "allOf": [
    {
      "prefixItems": [
        {
          "type": "string"
        }
      ],
      "items": true
    }
  ],
  "unevaluatedItems": false
}

### Results:
| Instance | swift-json-schema (swift) |
|:-----------------:|:-----:|
|      ["foo"]      | valid |
| ["foo", 42, true] | valid |### 303. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "allOf": [
    {
      "prefixItems": [
        {
          "type": "string"
        }
      ]
    },
    {
      "unevaluatedItems": true
    }
  ],
  "unevaluatedItems": false
}

### Results:
| Instance | swift-json-schema (swift) |
|:-----------------:|:-----:|
|      ["foo"]      | valid |
| ["foo", 42, true] | valid |### 304. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "prefixItems": [
    {
      "const": "foo"
    }
  ],
  "anyOf": [
    {
      "prefixItems": [
        true,
        {
          "const": "bar"
        }
      ]
    },
    {
      "prefixItems": [
        true,
        true,
        {
          "const": "baz"
        }
      ]
    }
  ],
  "unevaluatedItems": false
}

### Results:
| Instance | swift-json-schema (swift) |
|:-------------------------:|:-------:|
|       ["foo", "bar"]      |  valid  |
|     ["foo", "bar", 42]    | invalid |
|   ["foo", "bar", "baz"]   |  valid  |
| ["foo", "bar", "baz", 42] | invalid |### 305. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "prefixItems": [
    {
      "const": "foo"
    }
  ],
  "oneOf": [
    {
      "prefixItems": [
        true,
        {
          "const": "bar"
        }
      ]
    },
    {
      "prefixItems": [
        true,
        {
          "const": "baz"
        }
      ]
    }
  ],
  "unevaluatedItems": false
}

### Results:
| Instance | swift-json-schema (swift) |
|:------------------:|:-------:|
|   ["foo", "bar"]   |  valid  |
| ["foo", "bar", 42] | invalid |### 306. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "prefixItems": [
    {
      "const": "foo"
    }
  ],
  "not": {
    "not": {
      "prefixItems": [
        true,
        {
          "const": "bar"
        }
      ]
    }
  },
  "unevaluatedItems": false
}

### Results:
| Instance | swift-json-schema (swift) |
|:--------------:|:-------:|
| ["foo", "bar"] | invalid |### 307. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "prefixItems": [
    {
      "const": "foo"
    }
  ],
  "if": {
    "prefixItems": [
      true,
      {
        "const": "bar"
      }
    ]
  },
  "then": {
    "prefixItems": [
      true,
      true,
      {
        "const": "then"
      }
    ]
  },
  "else": {
    "prefixItems": [
      true,
      true,
      true,
      {
        "const": "else"
      }
    ]
  },
  "unevaluatedItems": false
}

### Results:
| Instance | swift-json-schema (swift) |
|:------------------------------:|:-------:|
|     ["foo", "bar", "then"]     |  valid  |
| ["foo", "bar", "then", "else"] | invalid |
|    ["foo", 42, 42, "else"]     |  valid  |
|  ["foo", 42, 42, "else", 42]   | invalid |### 308. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "allOf": [
    true
  ],
  "unevaluatedItems": false
}

### Results:
| Instance | swift-json-schema (swift) |
|:-------:|:-------:|
|    []   |  valid  |
| ["foo"] | invalid |### 309. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$ref": "#/$defs/bar",
  "prefixItems": [
    {
      "type": "string"
    }
  ],
  "unevaluatedItems": false,
  "$defs": {
    "bar": {
      "prefixItems": [
        true,
        {
          "type": "string"
        }
      ]
    }
  }
}

### Results:
| Instance | swift-json-schema (swift) |
|:---------------------:|:-------:|
|     ["foo", "bar"]    |  valid  |
| ["foo", "bar", "baz"] | invalid |### 310. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "unevaluatedItems": false,
  "prefixItems": [
    {
      "type": "string"
    }
  ],
  "$ref": "#/$defs/bar",
  "$defs": {
    "bar": {
      "prefixItems": [
        true,
        {
          "type": "string"
        }
      ]
    }
  }
}

### Results:
| Instance | swift-json-schema (swift) |
|:---------------------:|:-------:|
|     ["foo", "bar"]    |  valid  |
| ["foo", "bar", "baz"] | invalid |### 311. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://example.com/unevaluated-items-with-dynamic-ref/derived",
  "$ref": "./baseSchema",
  "$defs": {
    "derived": {
      "$dynamicAnchor": "addons",
      "prefixItems": [
        true,
        {
          "type": "string"
        }
      ]
    },
    "baseSchema": {
      "$id": "./baseSchema",
      "$comment": "unevaluatedItems comes first so it's more likely to catch bugs with implementations that are sensitive to keyword ordering",
      "unevaluatedItems": false,
      "type": "array",
      "prefixItems": [
        {
          "type": "string"
        }
      ],
      "$dynamicRef": "#addons",
      "$defs": {
        "defaultAddons": {
          "$comment": "Needed to satisfy the bookending requirement",
          "$dynamicAnchor": "addons"
        }
      }
    }
  }
}

### Results:
| Instance | swift-json-schema (swift) |
|:---------------------:|:-------:|
|     ["foo", "bar"]    | invalid |
| ["foo", "bar", "baz"] | invalid |### 312. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "allOf": [
    {
      "prefixItems": [
        true
      ]
    },
    {
      "unevaluatedItems": false
    }
  ]
}

### Results:
| Instance | swift-json-schema (swift) |
|:---:|:-------:|
| [1] | invalid |### 313. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "properties": {
    "foo": {
      "prefixItems": [
        {
          "type": "string"
        }
      ],
      "unevaluatedItems": false
    }
  },
  "anyOf": [
    {
      "properties": {
        "foo": {
          "prefixItems": [
            true,
            {
              "type": "string"
            }
          ]
        }
      }
    }
  ]
}

### Results:
| Instance | swift-json-schema (swift) |
|:-------------------------:|:-------:|
|     {"foo": ["test"]}     |  valid  |
| {"foo": ["test", "test"]} | invalid |### 314. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "prefixItems": [
    true
  ],
  "contains": {
    "type": "string"
  },
  "unevaluatedItems": false
}

### Results:
| Instance | swift-json-schema (swift) |
|:-------------:|:-------:|
|   [1, "foo"]  |  valid  |
|     [1, 2]    | invalid |
| [1, 2, "foo"] | invalid |### 315. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "allOf": [
    {
      "contains": {
        "multipleOf": 2
      }
    },
    {
      "contains": {
        "multipleOf": 3
      }
    }
  ],
  "unevaluatedItems": {
    "multipleOf": 5
  }
}

### Results:
| Instance | swift-json-schema (swift) |
|:---------------:|:-------:|
| [2, 3, 4, 5, 6] |  valid  |
| [2, 3, 4, 7, 8] | invalid |### 316. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "if": {
    "contains": {
      "const": "a"
    }
  },
  "then": {
    "if": {
      "contains": {
        "const": "b"
      }
    },
    "then": {
      "if": {
        "contains": {
          "const": "c"
        }
      }
    }
  },
  "unevaluatedItems": false
}

### Results:
| Instance | swift-json-schema (swift) |
|:------------------------------:|:-------:|
|               []               |  valid  |
|           ["a", "a"]           |  valid  |
|   ["a", "b", "a", "b", "a"]    |  valid  |
| ["c", "a", "c", "c", "b", "a"] |  valid  |
|           ["b", "b"]           | invalid |
|           ["c", "c"]           | invalid |
|   ["c", "b", "c", "b", "c"]    | invalid |
|   ["c", "a", "c", "a", "c"]    | invalid |### 317. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "unevaluatedItems": false
}

### Results:
| Instance | swift-json-schema (swift) |
|:-----:|:-----:|
|  true | valid |
|  123  | valid |
|  1.0  | valid |
|   {}  | valid |
| "foo" | valid |
|  null | valid |### 318. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "unevaluatedItems": {
    "type": "null"
  }
}

### Results:
| Instance | swift-json-schema (swift) |
|:------:|:-----:|
|  | valid |### 319. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "if": {
    "prefixItems": [
      {
        "const": "a"
      }
    ]
  },
  "unevaluatedItems": false
}

### Results:
| Instance | swift-json-schema (swift) |
|:-----:|:-------:|
| ["a"] |  valid  |
| ["b"] | invalid |### 320. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "unevaluatedProperties": true
}

### Results:
| Instance | swift-json-schema (swift) |
|:--------------:|:-----:|
|       {}       | valid |
| {"foo": "foo"} | valid |### 321. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "unevaluatedProperties": {
    "type": "string",
    "minLength": 3
  }
}

### Results:
| Instance | swift-json-schema (swift) |
|:--------------:|:-------:|
|       {}       |  valid  |
| {"foo": "foo"} |  valid  |
| {"foo": "fo"}  | invalid |### 322. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "unevaluatedProperties": false
}

### Results:
| Instance | swift-json-schema (swift) |
|:--------------:|:-------:|
|       {}       |  valid  |
| {"foo": "foo"} | invalid |### 323. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "properties": {
    "foo": {
      "type": "string"
    }
  },
  "unevaluatedProperties": false
}

### Results:
| Instance | swift-json-schema (swift) |
|:----------------------------:|:-------:|
|        {"foo": "foo"}        |  valid  |
| {"foo": "foo", "bar": "bar"} | invalid |### 324. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "patternProperties": {
    "^foo": {
      "type": "string"
    }
  },
  "unevaluatedProperties": false
}

### Results:
| Instance | swift-json-schema (swift) |
|:----------------------------:|:-------:|
|        {"foo": "foo"}        |  valid  |
| {"foo": "foo", "bar": "bar"} | invalid |### 325. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "additionalProperties": true,
  "unevaluatedProperties": false
}

### Results:
| Instance | swift-json-schema (swift) |
|:----------------------------:|:-----:|
|        {"foo": "foo"}        | valid |
| {"foo": "foo", "bar": "bar"} | valid |### 326. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "additionalProperties": {
    "type": "string"
  },
  "unevaluatedProperties": false
}

### Results:
| Instance | swift-json-schema (swift) |
|:------------------------:|:-------:|
|      {"foo": "foo"}      |  valid  |
| {"foo": "foo", "bar": 1} | invalid |### 327. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "properties": {
    "foo": {
      "type": "string"
    }
  },
  "allOf": [
    {
      "properties": {
        "bar": {
          "type": "string"
        }
      }
    }
  ],
  "unevaluatedProperties": false
}

### Results:
| Instance | swift-json-schema (swift) |
|:------------------------------------------:|:-------:|
|        {"foo": "foo", "bar": "bar"}        |  valid  |
| {"foo": "foo", "bar": "bar", "baz": "baz"} | invalid |### 328. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "properties": {
    "foo": {
      "type": "string"
    }
  },
  "allOf": [
    {
      "patternProperties": {
        "^bar": {
          "type": "string"
        }
      }
    }
  ],
  "unevaluatedProperties": false
}

### Results:
| Instance | swift-json-schema (swift) |
|:------------------------------------------:|:-------:|
|        {"foo": "foo", "bar": "bar"}        |  valid  |
| {"foo": "foo", "bar": "bar", "baz": "baz"} | invalid |### 329. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "properties": {
    "foo": {
      "type": "string"
    }
  },
  "allOf": [
    {
      "additionalProperties": true
    }
  ],
  "unevaluatedProperties": false
}

### Results:
| Instance | swift-json-schema (swift) |
|:----------------------------:|:-----:|
|        {"foo": "foo"}        | valid |
| {"foo": "foo", "bar": "bar"} | valid |### 330. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "properties": {
    "foo": {
      "type": "string"
    }
  },
  "allOf": [
    {
      "unevaluatedProperties": true
    }
  ],
  "unevaluatedProperties": {
    "type": "string",
    "maxLength": 2
  }
}

### Results:
| Instance | swift-json-schema (swift) |
|:----------------------------:|:-----:|
|        {"foo": "foo"}        | valid |
| {"foo": "foo", "bar": "bar"} | valid |### 331. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "properties": {
    "foo": {
      "type": "string"
    }
  },
  "anyOf": [
    {
      "properties": {
        "bar": {
          "const": "bar"
        }
      },
      "required": [
        "bar"
      ]
    },
    {
      "properties": {
        "baz": {
          "const": "baz"
        }
      },
      "required": [
        "baz"
      ]
    },
    {
      "properties": {
        "quux": {
          "const": "quux"
        }
      },
      "required": [
        "quux"
      ]
    }
  ],
  "unevaluatedProperties": false
}

### Results:
| Instance | swift-json-schema (swift) |
|:--------------------------------------------------------------:|:-------:|
|                  {"foo": "foo", "bar": "bar"}                  |  valid  |
|         {"foo": "foo", "bar": "bar", "baz": "not-baz"}         | invalid |
|           {"foo": "foo", "bar": "bar", "baz": "baz"}           |  valid  |
| {"foo": "foo", "bar": "bar", "baz": "baz", "quux": "not-quux"} | invalid |### 332. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "properties": {
    "foo": {
      "type": "string"
    }
  },
  "oneOf": [
    {
      "properties": {
        "bar": {
          "const": "bar"
        }
      },
      "required": [
        "bar"
      ]
    },
    {
      "properties": {
        "baz": {
          "const": "baz"
        }
      },
      "required": [
        "baz"
      ]
    }
  ],
  "unevaluatedProperties": false
}

### Results:
| Instance | swift-json-schema (swift) |
|:--------------------------------------------:|:-------:|
|         {"foo": "foo", "bar": "bar"}         |  valid  |
| {"foo": "foo", "bar": "bar", "quux": "quux"} | invalid |### 333. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "properties": {
    "foo": {
      "type": "string"
    }
  },
  "not": {
    "not": {
      "properties": {
        "bar": {
          "const": "bar"
        }
      },
      "required": [
        "bar"
      ]
    }
  },
  "unevaluatedProperties": false
}

### Results:
| Instance | swift-json-schema (swift) |
|:----------------------------:|:-------:|
| {"foo": "foo", "bar": "bar"} | invalid |### 334. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "if": {
    "properties": {
      "foo": {
        "const": "then"
      }
    },
    "required": [
      "foo"
    ]
  },
  "then": {
    "properties": {
      "bar": {
        "type": "string"
      }
    },
    "required": [
      "bar"
    ]
  },
  "else": {
    "properties": {
      "baz": {
        "type": "string"
      }
    },
    "required": [
      "baz"
    ]
  },
  "unevaluatedProperties": false
}

### Results:
| Instance | swift-json-schema (swift) |
|:-------------------------------------------:|:-------:|
|        {"foo": "then", "bar": "bar"}        |  valid  |
| {"foo": "then", "bar": "bar", "baz": "baz"} | invalid |
|                {"baz": "baz"}               |  valid  |
|        {"foo": "else", "baz": "baz"}        | invalid |### 335. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "if": {
    "properties": {
      "foo": {
        "const": "then"
      }
    },
    "required": [
      "foo"
    ]
  },
  "else": {
    "properties": {
      "baz": {
        "type": "string"
      }
    },
    "required": [
      "baz"
    ]
  },
  "unevaluatedProperties": false
}

### Results:
| Instance | swift-json-schema (swift) |
|:-------------------------------------------:|:-------:|
|        {"foo": "then", "bar": "bar"}        | invalid |
| {"foo": "then", "bar": "bar", "baz": "baz"} | invalid |
|                {"baz": "baz"}               |  valid  |
|        {"foo": "else", "baz": "baz"}        | invalid |### 336. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "if": {
    "properties": {
      "foo": {
        "const": "then"
      }
    },
    "required": [
      "foo"
    ]
  },
  "then": {
    "properties": {
      "bar": {
        "type": "string"
      }
    },
    "required": [
      "bar"
    ]
  },
  "unevaluatedProperties": false
}

### Results:
| Instance | swift-json-schema (swift) |
|:-------------------------------------------:|:-------:|
|        {"foo": "then", "bar": "bar"}        |  valid  |
| {"foo": "then", "bar": "bar", "baz": "baz"} | invalid |
|                {"baz": "baz"}               | invalid |
|        {"foo": "else", "baz": "baz"}        | invalid |### 337. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "properties": {
    "foo": {
      "type": "string"
    }
  },
  "dependentSchemas": {
    "foo": {
      "properties": {
        "bar": {
          "const": "bar"
        }
      },
      "required": [
        "bar"
      ]
    }
  },
  "unevaluatedProperties": false
}

### Results:
| Instance | swift-json-schema (swift) |
|:----------------------------:|:-------:|
| {"foo": "foo", "bar": "bar"} |  valid  |
|        {"bar": "bar"}        | invalid |### 338. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "properties": {
    "foo": {
      "type": "string"
    }
  },
  "allOf": [
    true
  ],
  "unevaluatedProperties": false
}

### Results:
| Instance | swift-json-schema (swift) |
|:--------------:|:-------:|
| {"foo": "foo"} |  valid  |
| {"bar": "bar"} | invalid |### 339. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$ref": "#/$defs/bar",
  "properties": {
    "foo": {
      "type": "string"
    }
  },
  "unevaluatedProperties": false,
  "$defs": {
    "bar": {
      "properties": {
        "bar": {
          "type": "string"
        }
      }
    }
  }
}

### Results:
| Instance | swift-json-schema (swift) |
|:------------------------------------------:|:-------:|
|        {"foo": "foo", "bar": "bar"}        |  valid  |
| {"foo": "foo", "bar": "bar", "baz": "baz"} | invalid |### 340. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "unevaluatedProperties": false,
  "properties": {
    "foo": {
      "type": "string"
    }
  },
  "$ref": "#/$defs/bar",
  "$defs": {
    "bar": {
      "properties": {
        "bar": {
          "type": "string"
        }
      }
    }
  }
}

### Results:
| Instance | swift-json-schema (swift) |
|:------------------------------------------:|:-------:|
|        {"foo": "foo", "bar": "bar"}        |  valid  |
| {"foo": "foo", "bar": "bar", "baz": "baz"} | invalid |### 341. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://example.com/unevaluated-properties-with-dynamic-ref/derived",
  "$ref": "./baseSchema",
  "$defs": {
    "derived": {
      "$dynamicAnchor": "addons",
      "properties": {
        "bar": {
          "type": "string"
        }
      }
    },
    "baseSchema": {
      "$id": "./baseSchema",
      "$comment": "unevaluatedProperties comes first so it's more likely to catch bugs with implementations that are sensitive to keyword ordering",
      "unevaluatedProperties": false,
      "properties": {
        "foo": {
          "type": "string"
        }
      },
      "$dynamicRef": "#addons",
      "$defs": {
        "defaultAddons": {
          "$comment": "Needed to satisfy the bookending requirement",
          "$dynamicAnchor": "addons"
        }
      }
    }
  }
}

### Results:
| Instance | swift-json-schema (swift) |
|:------------------------------------------:|:-------:|
|        {"foo": "foo", "bar": "bar"}        | invalid |
| {"foo": "foo", "bar": "bar", "baz": "baz"} | invalid |### 342. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "allOf": [
    {
      "properties": {
        "foo": true
      }
    },
    {
      "unevaluatedProperties": false
    }
  ]
}

### Results:
| Instance | swift-json-schema (swift) |
|:----------:|:-------:|
| {"foo": 1} | invalid |### 343. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "allOf": [
    {
      "unevaluatedProperties": false
    },
    {
      "properties": {
        "foo": true
      }
    }
  ]
}

### Results:
| Instance | swift-json-schema (swift) |
|:----------:|:-------:|
| {"foo": 1} | invalid |### 344. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "properties": {
    "foo": {
      "type": "string"
    }
  },
  "allOf": [
    {
      "unevaluatedProperties": true
    }
  ],
  "unevaluatedProperties": false
}

### Results:
| Instance | swift-json-schema (swift) |
|:----------------------------:|:-----:|
|        {"foo": "foo"}        | valid |
| {"foo": "foo", "bar": "bar"} | valid |### 345. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "allOf": [
    {
      "properties": {
        "foo": {
          "type": "string"
        }
      },
      "unevaluatedProperties": true
    }
  ],
  "unevaluatedProperties": false
}

### Results:
| Instance | swift-json-schema (swift) |
|:----------------------------:|:-----:|
|        {"foo": "foo"}        | valid |
| {"foo": "foo", "bar": "bar"} | valid |### 346. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "properties": {
    "foo": {
      "type": "string"
    }
  },
  "allOf": [
    {
      "unevaluatedProperties": false
    }
  ],
  "unevaluatedProperties": true
}

### Results:
| Instance | swift-json-schema (swift) |
|:----------------------------:|:-------:|
|        {"foo": "foo"}        | invalid |
| {"foo": "foo", "bar": "bar"} | invalid |### 347. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "allOf": [
    {
      "properties": {
        "foo": {
          "type": "string"
        }
      },
      "unevaluatedProperties": false
    }
  ],
  "unevaluatedProperties": true
}

### Results:
| Instance | swift-json-schema (swift) |
|:----------------------------:|:-------:|
|        {"foo": "foo"}        |  valid  |
| {"foo": "foo", "bar": "bar"} | invalid |### 348. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "allOf": [
    {
      "properties": {
        "foo": {
          "type": "string"
        }
      },
      "unevaluatedProperties": true
    },
    {
      "unevaluatedProperties": false
    }
  ]
}

### Results:
| Instance | swift-json-schema (swift) |
|:----------------------------:|:-------:|
|        {"foo": "foo"}        | invalid |
| {"foo": "foo", "bar": "bar"} | invalid |### 349. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "allOf": [
    {
      "unevaluatedProperties": true
    },
    {
      "properties": {
        "foo": {
          "type": "string"
        }
      },
      "unevaluatedProperties": false
    }
  ]
}

### Results:
| Instance | swift-json-schema (swift) |
|:----------------------------:|:-------:|
|        {"foo": "foo"}        |  valid  |
| {"foo": "foo", "bar": "bar"} | invalid |### 350. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "properties": {
    "foo": {
      "properties": {
        "bar": {
          "type": "string"
        }
      },
      "unevaluatedProperties": false
    }
  },
  "anyOf": [
    {
      "properties": {
        "foo": {
          "properties": {
            "faz": {
              "type": "string"
            }
          }
        }
      }
    }
  ]
}

### Results:
| Instance | swift-json-schema (swift) |
|:---------------------------------------:|:-------:|
|         {"foo": {"bar": "test"}}        |  valid  |
| {"foo": {"bar": "test", "faz": "test"}} | invalid |### 351. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "allOf": [
    {
      "properties": {
        "foo": true
      },
      "unevaluatedProperties": false
    }
  ],
  "anyOf": [
    {
      "properties": {
        "bar": true
      }
    }
  ]
}

### Results:
| Instance | swift-json-schema (swift) |
|:--------------------:|:-------:|
| {"foo": 1, "bar": 1} | invalid |
|      {"foo": 1}      |  valid  |
|      {"bar": 1}      | invalid |### 352. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "allOf": [
    {
      "properties": {
        "foo": true
      }
    }
  ],
  "anyOf": [
    {
      "properties": {
        "bar": true
      },
      "unevaluatedProperties": false
    }
  ]
}

### Results:
| Instance | swift-json-schema (swift) |
|:--------------------:|:-------:|
| {"foo": 1, "bar": 1} | invalid |
|      {"foo": 1}      | invalid |
|      {"bar": 1}      |  valid  |### 353. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "properties": {
    "x": {
      "$ref": "#"
    }
  },
  "unevaluatedProperties": false
}

### Results:
| Instance | swift-json-schema (swift) |
|:--------------------------------:|:-------:|
|                {}                |  valid  |
|            {"x": {}}             |  valid  |
|        {"x": {}, "y": {}}        | invalid |
|         {"x": {"x": {}}}         |  valid  |
|    {"x": {"x": {}, "y": {}}}     | invalid |
|     {"x": {"x": {"x": {}}}}      |  valid  |
| {"x": {"x": {"x": {}, "y": {}}}} | invalid |### 354. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$defs": {
    "one": {
      "properties": {
        "a": true
      }
    },
    "two": {
      "required": [
        "x"
      ],
      "properties": {
        "x": true
      }
    }
  },
  "allOf": [
    {
      "$ref": "#/$defs/one"
    },
    {
      "properties": {
        "b": true
      }
    },
    {
      "oneOf": [
        {
          "$ref": "#/$defs/two"
        },
        {
          "required": [
            "y"
          ],
          "properties": {
            "y": true
          }
        }
      ]
    }
  ],
  "unevaluatedProperties": false
}

### Results:
| Instance | swift-json-schema (swift) |
|:--------------------------------:|:-------:|
|                {}                | invalid |
|         {"a": 1, "b": 1}         | invalid |
|         {"x": 1, "y": 1}         | invalid |
|         {"a": 1, "x": 1}         |  valid  |
|         {"a": 1, "y": 1}         |  valid  |
|     {"a": 1, "b": 1, "x": 1}     |  valid  |
|     {"a": 1, "b": 1, "y": 1}     |  valid  |
| {"a": 1, "b": 1, "x": 1, "y": 1} | invalid |### 355. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$defs": {
    "one": {
      "oneOf": [
        {
          "$ref": "#/$defs/two"
        },
        {
          "required": [
            "b"
          ],
          "properties": {
            "b": true
          }
        },
        {
          "required": [
            "xx"
          ],
          "patternProperties": {
            "x": true
          }
        },
        {
          "required": [
            "all"
          ],
          "unevaluatedProperties": true
        }
      ]
    },
    "two": {
      "oneOf": [
        {
          "required": [
            "c"
          ],
          "properties": {
            "c": true
          }
        },
        {
          "required": [
            "d"
          ],
          "properties": {
            "d": true
          }
        }
      ]
    }
  },
  "oneOf": [
    {
      "$ref": "#/$defs/one"
    },
    {
      "required": [
        "a"
      ],
      "properties": {
        "a": true
      }
    }
  ],
  "unevaluatedProperties": false
}

### Results:
| Instance | swift-json-schema (swift) |
|:--------------------:|:-------:|
|          {}          | invalid |
|       {"a": 1}       |  valid  |
|       {"b": 1}       |  valid  |
|       {"c": 1}       |  valid  |
|       {"d": 1}       |  valid  |
|   {"a": 1, "b": 1}   | invalid |
|   {"a": 1, "c": 1}   | invalid |
|   {"a": 1, "d": 1}   | invalid |
|   {"b": 1, "c": 1}   | invalid |
|   {"b": 1, "d": 1}   | invalid |
|   {"c": 1, "d": 1}   | invalid |
|      {"xx": 1}       |  valid  |
| {"xx": 1, "foox": 1} |  valid  |
| {"xx": 1, "foo": 1}  | invalid |
|  {"xx": 1, "a": 1}   | invalid |
|  {"xx": 1, "b": 1}   | invalid |
|  {"xx": 1, "c": 1}   | invalid |
|  {"xx": 1, "d": 1}   | invalid |
|      {"all": 1}      |  valid  |
| {"all": 1, "foo": 1} |  valid  |
|  {"all": 1, "a": 1}  | invalid |### 356. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "unevaluatedProperties": false
}

### Results:
| Instance | swift-json-schema (swift) |
|:-----:|:-----:|
|  true | valid |
|  123  | valid |
|  1.0  | valid |
|   []  | valid |
| "foo" | valid |
|  null | valid |### 357. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "unevaluatedProperties": {
    "type": "null"
  }
}

### Results:
| Instance | swift-json-schema (swift) |
|:-------------:|:-----:|
| {"foo": null} | valid |### 358. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "propertyNames": {
    "maxLength": 1
  },
  "unevaluatedProperties": {
    "type": "number"
  }
}

### Results:
| Instance | swift-json-schema (swift) |
|:----------:|:-------:|
|  {"a": 1}  |  valid  |
| {"a": "b"} | invalid |### 359. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "if": {
    "patternProperties": {
      "foo": {
        "type": "string"
      }
    }
  },
  "unevaluatedProperties": false
}

### Results:
| Instance | swift-json-schema (swift) |
|:------------:|:-------:|
| {"foo": "a"} |  valid  |
| {"bar": "a"} | invalid |### 360. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "properties": {
    "foo2": {}
  },
  "dependentSchemas": {
    "foo": {},
    "foo2": {
      "properties": {
        "bar": {}
      }
    }
  },
  "unevaluatedProperties": false
}

### Results:
| Instance | swift-json-schema (swift) |
|:-----------------------:|:-------:|
|       {"foo": ""}       | invalid |
|       {"bar": ""}       | invalid |
| {"foo2": "", "bar": ""} |  valid  |### 361. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "uniqueItems": true
}

### Results:
| Instance | swift-json-schema (swift) |
|:-------------------------------------------------------------------:|:-------:|
|                                [1, 2]                               |  valid  |
|                                [1, 1]                               | invalid |
|                              [1, 2, 1]                              | invalid |
|                            [1.0, 1.0, 1]                            | invalid |
|                              [0, false]                             |  valid  |
|                              [1, true]                              |  valid  |
|                        ["foo", "bar", "baz"]                        |  valid  |
|                        ["foo", "bar", "foo"]                        | invalid |
|                   [{"foo": "bar"}, {"foo": "baz"}]                  |  valid  |
|                   [{"foo": "bar"}, {"foo": "bar"}]                  | invalid |
|     [{"foo": "bar", "bar": "foo"}, {"bar": "foo", "foo": "bar"}]    | invalid |
| [{"foo": {"bar": {"baz": true}}}, {"foo": {"bar": {"baz": false}}}] |  valid  |
|  [{"foo": {"bar": {"baz": true}}}, {"foo": {"bar": {"baz": true}}}] | invalid |
|                          [["foo"], ["bar"]]                         |  valid  |
|                          [["foo"], ["foo"]]                         | invalid |
|                     [["foo"], ["bar"], ["foo"]]                     | invalid |
|                              [1, true]                              |  valid  |
|                              [0, false]                             |  valid  |
|                            [[1], ]                            |  valid  |
|                            [[0], ]                           |  valid  |
|                   [[[1], "foo"], [, "foo"]]                   |  valid  |
|                   [[[0], "foo"], [, "foo"]]                  |  valid  |
|                    [{}, [1], true, null, 1, "{}"]                   |  valid  |
|                     [{}, [1], true, null, {}, 1]                    | invalid |
|                 [{"a": 1, "b": 2}, {"a": 2, "b": 1}]                |  valid  |
|                 [{"a": 1, "b": 2}, {"b": 2, "a": 1}]                | invalid |
|                       [{"a": false}, {"a": 0}]                      |  valid  |
|                       [{"a": true}, {"a": 1}]                       |  valid  |### 362. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "prefixItems": [
    {
      "type": "boolean"
    },
    {
      "type": "boolean"
    }
  ],
  "uniqueItems": true
}

### Results:
| Instance | swift-json-schema (swift) |
|:---------------------------:|:-------:|
|                |  valid  |
|                |  valid  |
|               | invalid |
|                 | invalid |
|  |  valid  |
|  |  valid  |
|  | invalid |
|  | invalid |### 363. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "prefixItems": [
    {
      "type": "boolean"
    },
    {
      "type": "boolean"
    }
  ],
  "uniqueItems": true,
  "items": false
}

### Results:
| Instance | swift-json-schema (swift) |
|:-------------------:|:-------:|
|        |  valid  |
|        |  valid  |
|       | invalid |
|         | invalid |
|  | invalid |### 364. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "uniqueItems": false
}

### Results:
| Instance | swift-json-schema (swift) |
|:-------------------------------------------------------------------:|:-----:|
|                                [1, 2]                               | valid |
|                                [1, 1]                               | valid |
|                            [1.0, 1.0, 1]                            | valid |
|                              [0, false]                             | valid |
|                              [1, true]                              | valid |
|                   [{"foo": "bar"}, {"foo": "baz"}]                  | valid |
|                   [{"foo": "bar"}, {"foo": "bar"}]                  | valid |
| [{"foo": {"bar": {"baz": true}}}, {"foo": {"bar": {"baz": false}}}] | valid |
|  [{"foo": {"bar": {"baz": true}}}, {"foo": {"bar": {"baz": true}}}] | valid |
|                          [["foo"], ["bar"]]                         | valid |
|                          [["foo"], ["foo"]]                         | valid |
|                              [1, true]                              | valid |
|                              [0, false]                             | valid |
|                       [{}, [1], true, null, 1]                      | valid |
|                     [{}, [1], true, null, {}, 1]                    | valid |### 365. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "prefixItems": [
    {
      "type": "boolean"
    },
    {
      "type": "boolean"
    }
  ],
  "uniqueItems": false
}

### Results:
| Instance | swift-json-schema (swift) |
|:---------------------------:|:-----:|
|                | valid |
|                | valid |
|               | valid |
|                 | valid |
|  | valid |
|  | valid |
|  | valid |
|  | valid |### 366. Schema:
 {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "prefixItems": [
    {
      "type": "boolean"
    },
    {
      "type": "boolean"
    }
  ],
  "uniqueItems": false,
  "items": false
}

### Results:
| Instance | swift-json-schema (swift) |
|:-------------------:|:-------:|
|        |  valid  |
|        |  valid  |
|       |  valid  |
|         |  valid  |
|  | invalid |### 367. Schema:
 {
  "$id": "https://schema/using/no/validation",
  "$schema": "http://localhost:1234/draft2020-12/metaschema-no-validation.json",
  "properties": {
    "badProperty": false,
    "numberProperty": {
      "minimum": 10
    }
  }
}

### Results:
| Instance | swift-json-schema (swift) |
|:-------------------------------------------------:|:-------:|
| {"badProperty": "this property should not exist"} | invalid |
|               {"numberProperty": 20}              |  valid  |
|               {"numberProperty": 1}               | invalid |### 368. Schema:
 {
  "$schema": "http://localhost:1234/draft2020-12/metaschema-optional-vocabulary.json",
  "type": "number"
}

### Results:
| Instance | swift-json-schema (swift) |
|:--------:|:-------:|
| "foobar" | invalid |
|    20    |  valid  |
