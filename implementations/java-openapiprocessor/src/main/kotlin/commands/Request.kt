package commands

import com.fasterxml.jackson.annotation.JsonSubTypes
import com.fasterxml.jackson.annotation.JsonTypeInfo

@JsonTypeInfo(
    use = JsonTypeInfo.Id.NAME,
    include = JsonTypeInfo.As.EXISTING_PROPERTY,
    property = "cmd",
)
@JsonSubTypes(
    JsonSubTypes.Type(name = "start", value = StartRequest::class),
    JsonSubTypes.Type(name = "stop", value = StopRequest::class),
    JsonSubTypes.Type(name = "dialect", value = DialectRequest::class),
    JsonSubTypes.Type(name = "run", value = RunRequest::class),
)
interface Request
