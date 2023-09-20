import java.util.*;
import java.util.logging.Level;
import java.util.logging.Logger;
import org.json.simple.JSONArray;
import org.json.simple.JSONObject;
import org.json.simple.parser.JSONParser;
import main.MainClass$;
import java.io.StringWriter;
import java.io.PrintWriter;
import scala.Tuple2;
import java.io.*;
import io.circe.Json;
import java.util.jar.Attributes;
import java.util.jar.Manifest;

/**
* The Harness program implements an application that
* simply take input from Bowtie application using standard
* input and output to the standard output.
*
* @author  Sajal Jain
* @version 1.0
* @since   2023-01-10 
*/
class Harness{
	
	public static boolean started = false;
	
	private static final Logger LOGGER = Logger.getLogger( Harness.class.getName() );
	
	public static String dialect;
	
	private static final String NOT_IMPLEMENTED = "This case is not yet implemented.";
	private static final Map<String, String> UNSUPPORTED_CASES = Map.ofEntries(
		Map.entry("escaped pointer ref", NOT_IMPLEMENTED), Map.entry("empty tokens in $ref json-pointer", NOT_IMPLEMENTED),
		Map.entry("maxLength validation", NOT_IMPLEMENTED),Map.entry("minLength validation", NOT_IMPLEMENTED),
		Map.entry("$id inside an unknown keyword is not a real identifier", NOT_IMPLEMENTED), Map.entry("schema that uses custom metaschema with with no validation vocabulary", NOT_IMPLEMENTED),
		Map.entry("small multiple of large integer", NOT_IMPLEMENTED), Map.entry("$ref to $ref finds detached $anchor", NOT_IMPLEMENTED),
		Map.entry("$ref to $dynamicRef finds detached $dynamicAnchor", NOT_IMPLEMENTED));
	
	public static void main(String[] args) {
		Scanner input = new Scanner(System.in);
		while (true) {
			String line = input.nextLine();
			String output = new Harness().operate(line);
			System.out.println(output);
		}
	}
	
	public String operate(String line){
		JSONParser parser = new JSONParser();
		String error = "";
		try{
			JSONObject json = (JSONObject) parser.parse(line);
			String cmd = (String) json.get("cmd");
			switch(cmd) {
			  case "start":
				long version = (long) json.get("version");
				if(version == 1){
					InputStream is = getClass().getResourceAsStream("META-INF/MANIFEST.MF");
					var attributes = new Manifest(is).getMainAttributes();
					started = true;
					JSONObject message = new JSONObject();
					message.put("ready", true);
					message.put("version", 1);
					JSONObject implementation = new JSONObject();
					implementation.put("language", "scala");
					implementation.put("name", attributes.getValue("Implementation-Name"));
					implementation.put("version", attributes.getValue("Implementation-Version"));
					implementation.put("homepage", "https://gitlab.lip6.fr/jsonschema/modernjsonschemavalidator");
					implementation.put("issues", "https://gitlab.lip6.fr/jsonschema/modernjsonschemavalidator/issues");
					JSONArray dialects = new JSONArray();
					dialects.add("https://json-schema.org/draft/2020-12/schema");
					implementation.put("dialects", dialects);
					message.put("implementation", implementation);
					return message.toJSONString();
				}
				break;
			  case "dialect":
				if(started != true){
					throw new RuntimeException("Bowtie hasn't started!");
				}
				dialect = (String) json.get("dialect");
				return "{ \"ok\" : false }";
			  case "run":
				if(started != true){
					throw new RuntimeException("Bowtie hasn't started!");
				}
				long seq = (long) json.get("seq");
				JSONObject test = null;
				JSONObject cas = null;
				String schema = null;
				String description = null;
				try{
					cas = (JSONObject) json.get("case");
					schema = getStringFromJson(cas.get("schema"));
					description = (String) cas.get("description");
					if(UNSUPPORTED_CASES.containsKey(description)){
						return skipMsg(UNSUPPORTED_CASES.get(description), seq);
					}
					JSONArray tests = (JSONArray) cas.get("tests");
					
					JSONArray resultArray = new JSONArray();
					Iterator testIterator = tests.iterator(); 
					
					while (testIterator.hasNext()) { 
						test = (JSONObject) testIterator.next();
						Object obj = test.get("instance");
						String instance = getStringFromJson(obj);
						MainClass$ m = MainClass$.MODULE$;
						Tuple2<Object, Json> results = m.validateInstance(schema, instance);
						boolean value = (boolean) results._1();
						
						JSONObject result = new JSONObject();
						result.put("valid", value);
						resultArray.add(result);
					}
					
					JSONObject output = new JSONObject();
					output.put("seq", seq);
					output.put("results", resultArray);
					return output.toJSONString();
				}
				catch(Exception e){
					LOGGER.log(Level.SEVERE, "Exception occur in run command : " + cas.toJSONString() + " " + test.toJSONString(), e);
					String msg = getDetailedMessage(e, test, schema);
					error = errorMsg(msg, seq);
					return error;
				}
			  case "stop":
				if(started != true){
					throw new RuntimeException("Bowtie hasn't started!");
				}
				System.exit(0);
			}
		}catch(Exception e){
			LOGGER.log(Level.SEVERE, "Exception occur in operate : ", e);
			error = errorMsg(e.getMessage(), -1);
			return error;
		}
		error = errorMsg("Send correct command", -1);
		return error;
	}
	
	public static String errorMsg(String message, long seq){
		JSONObject traceBack = new JSONObject(); 
		traceBack.put("traceBack", message);
		JSONObject error = new JSONObject(); 
		error.put("errored", true);
		error.put("seq", seq);
		error.put("context",traceBack);
		return error.toJSONString();
	}
	
	public static String skipMsg(String message, long seq){
		JSONObject traceBack = new JSONObject();
		JSONObject error = new JSONObject();
		error.put("skipped", true);
		error.put("seq", seq);
		error.put("message",message);
		return error.toJSONString();
	}
	
	public static String getDetailedMessage(Exception e, JSONObject test, String schema){
		StringWriter sw = new StringWriter();
		e.printStackTrace(new PrintWriter(sw));
		Object obj = test.get("instance");
		String instance = getStringFromJson(obj);
		return sw.toString() + " " + test.toJSONString() + " " + instance + " " + schema;
	}
	
	public static String getStringFromJson(Object obj){
		String value = "";
		if(obj == null) {
			value = "null";
		}
		else if (obj instanceof Long) {
			value = String.valueOf((Long)obj);
		}
		else if (obj instanceof Double) {
			value = String.valueOf((Double)obj);
		}
		else if (obj instanceof Boolean) {
			value = String.valueOf((Boolean)obj);
		}
		else if (obj instanceof String) {
			value = (String)obj;
			JSONObject json = new JSONObject();
			value = "\"" + json.escape(value) + "\"";
		}
		else if (obj instanceof JSONObject) {
			value = ((JSONObject)obj).toJSONString();
		}
		else if (obj instanceof JSONArray) {
			value = ((JSONArray)obj).toJSONString();
		}
		return value;
	}
}
