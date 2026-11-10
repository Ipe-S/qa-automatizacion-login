package cl.empresa.qa.bdd;

import org.junit.platform.suite.api.ConfigurationParameter;
import org.junit.platform.suite.api.IncludeEngines;
import org.junit.platform.suite.api.SelectClasspathResource;
import org.junit.platform.suite.api.Suite;

import static io.cucumber.junit.platform.engine.Constants.GLUE_PROPERTY_NAME;
import static io.cucumber.junit.platform.engine.Constants.PLUGIN_PROPERTY_NAME;

/**
 * Runner de los escenarios BDD. Termina en "IT" para que lo ejecute el plugin
 * Failsafe en la fase "verify", separado de las pruebas unitarias.
 * Genera reportes HTML (navegable), JSON (para el dashboard) y JUnit XML.
 */
@Suite
@IncludeEngines("cucumber")
@SelectClasspathResource("features")
@ConfigurationParameter(key = GLUE_PROPERTY_NAME, value = "cl.empresa.qa.bdd.steps")
@ConfigurationParameter(key = PLUGIN_PROPERTY_NAME, value = "pretty,"
        + "html:target/cucumber-reports/cucumber.html,"
        + "json:target/cucumber-reports/cucumber.json,"
        + "junit:target/cucumber-reports/cucumber.xml")
public class RunCucumberIT {
}
