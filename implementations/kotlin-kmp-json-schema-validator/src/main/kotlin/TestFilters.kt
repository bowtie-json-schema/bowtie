import io.github.optimumcode.json.schema.SchemaType

interface TestFilter {
    /**
     * @return reason if test case should be skipped
     */
    fun shouldSkipCase(caseDescription: String): String? = null

    /**
     * @return reason if test in test case should be skipped
     */
    fun shouldSkipTest(caseDescription: String, testDescription: String): String? = null
}

fun getFilter(schemaType: SchemaType?): TestFilter =
    when (schemaType ?: SchemaType.entries.last()) {
        SchemaType.DRAFT_7 -> TestFilterDraft7
        SchemaType.DRAFT_2019_09 -> TestFilterDraft201909
    }

object TestFilterDraft7 : TestFilter {
    /**
     * All these cases are ignored because they contain remote refs
     * Library does not support them yet.
     */
    private val IGNORED_CASES: Set<String> = hashSetOf(
        "validate definition against metaschema",
        "base URI change - change folder",
        "base URI change - change folder in subschema",
        "base URI change",
        "retrieved nested refs resolve relative to their URI not \$id",
        "\$ref to \$ref finds location-independent \$id",
    )

    override fun shouldSkipCase(caseDescription: String): String? {
        return when {
            caseDescription.endsWith(" format") -> "the format keyword is not yet supported"
            caseDescription in IGNORED_CASES || caseDescription.contains("remote ref") ->
                "remote schema loading is not yet supported"

            else -> null
        }
    }
}

object TestFilterDraft201909 : TestFilter {
    /**
     * All these cases are ignored because they contain remote refs or meta schema
     * Library does not support them yet.
     */
    private val IGNORED_CASES_WITH_REMOTE_REF: Set<String> = hashSetOf(
        "invalid anchors",
        "Invalid use of fragments in location-independent \$id",
        "Valid use of empty fragments in location-independent \$id",
        "Unnormalized \$ids are allowed but discouraged",
        "URN base URI with f-component",
        "remote HTTP ref with different \$id",
        "remote HTTP ref with different URN \$id",
        "remote HTTP ref with nested absolute ref",
        "\$ref to \$ref finds detached \$anchor",
        "schema that uses custom metaschema with with no validation vocabulary",
        "ignore unrecognized optional vocabulary",
        "validate definition against metaschema",
        "retrieved nested refs resolve relative to their URI not \$id",
        "base URI change - change folder in subschema",
        "base URI change - change folder",
        "base URI change",
    )

    private val IGNORE_CASES_WITH_MIN_CONTAINS_ZERO = setOf(
        "minContains = 0 with no maxContains"
    )

    override fun shouldSkipCase(caseDescription: String): String? {
        return when {
            caseDescription.endsWith(" format") -> "the format keyword is not yet supported"
            caseDescription in IGNORED_CASES_WITH_REMOTE_REF || caseDescription.contains("remote ref") ->
                "remote schema loading and meta schemas are not yet supported"
            caseDescription in IGNORE_CASES_WITH_MIN_CONTAINS_ZERO ->
                "'minContains' does not affect contains work - at least one element must match 'contains' schema"
            else -> null
        }
    }

    override fun shouldSkipTest(caseDescription: String, testDescription: String): String? {
        return when {
            caseDescription == "minContains = 0 with maxContains" &&
                    testDescription == "empty data" ->
                        "'minContains' does not affect contains work - at least one element must match 'contains' schema"
            else -> null
        }
    }
}
