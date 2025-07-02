import sqlite3
from mcp.server.fastmcp import FastMCP
import logging
logger = logging.getLogger(__name__)

# --- Server Definition ---
mcp = FastMCP(name="CYBER_SECURITY_SERVER")

conn = sqlite3.connect('databahn/mcp_servers/data/cybersecurity_mcp.db')


@mcp.tool()
def get_cybser_security_info(sql_query: str) -> str:
    """
    Execute SQL queries safely
    Here is the description of tables handled by this tool.
    You can join tables in your sql_query if required to retrieve the required information
    for regions if countries are provided then do a fuzzy search on continent of the country.
    <table_description>{        
    "cloud": {
        "columns": {
            "cloud_provider": "The name of the cloud service provider (e.g., AWS, Azure, GCP). For example: 'GCP'",
            "misconfiguration": "The specific type of security misconfiguration identified. For example: 'Unrestricted Network Security Group'",
            "threat_vector": "The potential attack path that could exploit the misconfiguration. For example: 'Denial of Service'",
            "recommendation": "The suggested action to remediate the misconfiguration. For example: 'Review and restrict S3 bucket policies to ensure no public access.'",
            "cve_id": "The common CVE identifier, used for joining with other tables. For example: 'CVE-2024-60850'"
        }
    },
    "darkweb": {
        "columns": {
            "forum": "The dark web forum or marketplace where the information was found. For example: 'XSS.is'",
            "post_type": "The category of the post (e.g., Leaked Credentials, Malware for Sale). For example: 'Vulnerability Exploit'",
            "summary": "A brief summary of the content of the dark web post. For example: 'A zero-day exploit for a popular software is available.'",
            "confidence": "The confidence level in the credibility of the post (e.g., Low, High). For example: 'Low'",
            "cve_id": "The common CVE identifier, used for joining with other tables. For example: 'CVE-2024-60850'"
        }
    },
    "geopolitical": {
        "columns": {
            "region": "The geographical region associated with the threat. For example: 'Middle East'",
            "threat_group": "The name of the Advanced Persistent Threat (APT) or other threat group. For example: 'OilRig (APT34)'",
            "targeted_sector": "The industry or sector being targeted by the threat group. For example: 'Government, Energy'",
            "activity_summary": "A summary of the observed activities of the threat group. For example: 'Espionage activity focused on intellectual property theft from tech companies.'",
            "cve_id": "The common CVE identifier, used for joining with other tables. For example: 'CVE-2024-60850'"
        }
    },
    "threat_intel": {
        "columns": {
            "threat_actors": "The names of known threat actors or groups. For example: 'Lazarus Group'",
            "latest_malware": "The names of recently identified malware families. For example: 'TrickBot'",
            "global_alerts": "High-level security alerts about ongoing campaigns or major vulnerabilities. For example: 'Alert: Zero-day vulnerability discovered in popular web browser.'",
            "cve_id": "The common CVE identifier associated with the alert, used for joining with other tables. For example: 'CVE-2024-60850'"
        }
    },
    "vulnerability": {
        "columns": {
            "cve_id": "The unique Common Vulnerabilities and Exposures identifier. This can be used as a primary key to join with other tables. For example: 'CVE-2024-60850'",
            "product": "The name of the product or software affected by the vulnerability. For example: 'WinRAR'",
            "description": "A detailed description of the vulnerability. For example: 'A remote code execution vulnerability exists in the web server.'",
            "cvss_score": "The Common Vulnerability Scoring System score (0.0-10.0), indicating severity. For example: '8.1'"
        }
    }
    }</table_description>
    """
    print(f"The incoming SQL query: {sql_query}")

    try:
        result = conn.execute(sql_query).fetchall()
        conn.commit()
        return "\n".join(str(row) for row in result)
    except Exception as e:
        return ValueError

if __name__ == '__main__':
    print("Starting server...")
    # Initialize and run the server
    mcp.run(transport="stdio")
