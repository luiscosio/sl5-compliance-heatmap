#!/usr/bin/env python3
"""
SL5 Stakeholder Network Data Scraper
Gathers comprehensive information about AI labs, contractors, security personnel, and infrastructure providers
using Claude API with web search capabilities.
"""

import json
import anthropic
import time
import argparse
import os
import sys
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# --- Configuration ---
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
CLAUDE_MODEL = "claude-sonnet-4-20250514"
OUTPUT_FILE = "data/sl5-stakeholder-network.json"

# Primary AI Labs to investigate
AI_LABS = ["OpenAI", "Anthropic", "Google DeepMind", "xAI", "Meta AI"]

# Categories of stakeholders to research
STAKEHOLDER_CATEGORIES = [
    "datacenter_contractors",
    "security_personnel", 
    "cloud_infrastructure",  # Combined CSP and hyperscaler
    "power_infrastructure",
    "hardware_suppliers",
    "security_contractors"
]

# Initialize Anthropic client
client = None
if ANTHROPIC_API_KEY:
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
else:
    print("ERROR: ANTHROPIC_API_KEY environment variable is not set.", file=sys.stderr)
    sys.exit(1)

def create_node(node_id: str, name: str, category: str, description: str = "", 
                size: int = 20, url: str = "", research: List[str] = None, 
                sources: List[Dict] = None) -> Dict:
    """Create a node object for the network graph."""
    return {
        "id": node_id,
        "name": name,
        "category": category,
        "description": description,
        "size": size,
        "url": url,
        "research": research or [],
        "sources": sources or []
    }

def create_link(source: str, target: str, strength: int = 3) -> Dict:
    """Create a link object for the network graph."""
    return {
        "source": source,
        "target": target,
        "strength": strength
    }

def parse_json_from_response(text: str) -> Optional[Dict]:
    """Extract JSON from Claude's response, handling markdown code blocks."""
    # Try to find JSON in code blocks first
    json_pattern = re.compile(r"```(?:json)?\s*(\{.*?\}|\[.*?\])\s*```", re.DOTALL)
    match = json_pattern.search(text)
    
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            print(f"Failed to parse JSON from code block", file=sys.stderr)
    
    # Try to find raw JSON in the text
    try:
        # Find JSON-like structures
        json_start = text.find('{')
        if json_start >= 0:
            json_end = text.rfind('}') + 1
            if json_end > json_start:
                return json.loads(text[json_start:json_end])
    except json.JSONDecodeError:
        pass
    
    return None

def search_datacenter_contractors(ai_lab: str) -> Dict:
    """Search for datacenter contractors working with a specific AI lab."""
    query_prompt = f"""
    Search for information about datacenter construction contractors working with {ai_lab}. 
    Focus on:
    1. Which contractors are building datacenters for {ai_lab}
    2. Specific projects (size, location, timeline)
    3. Specializations (SCIF construction, hyperscale, edge computing)
    4. Contract values if available
    5. Which other AI companies they work with
    
    For Meta specifically, find information about their 5GW datacenter projects and contractors.
    
    Provide response as JSON with this structure:
    {{
        "contractors": [
            {{
                "name": "Company Name",
                "description": "Brief description including specializations",
                "projects": ["Project details"],
                "specializations": ["SCIF", "Hyperscale", etc],
                "contract_value": "If known",
                "other_clients": ["Other AI labs they work with"],
                "url": "Company website",
                "sources": ["URL1", "URL2"]
            }}
        ]
    }}
    """
    
    try:
        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=2048,
            messages=[{"role": "user", "content": query_prompt}],
            tools=[{
                "type": "web_search_20250305",
                "name": "web_search",
                "max_uses": 5
            }]
        )
        
        for content_block in response.content:
            if content_block.type == "text":
                result = parse_json_from_response(content_block.text)
                if result:
                    return result
        
        return {"contractors": []}
        
    except Exception as e:
        print(f"Error searching contractors for {ai_lab}: {e}", file=sys.stderr)
        return {"contractors": []}

def search_security_personnel(ai_lab: str) -> Dict:
    """Search for senior security staff at AI labs."""
    query_prompt = f"""
    Search for information about senior security personnel at {ai_lab}. 
    Focus on:
    1. Chief Information Security Officer (CISO)
    2. VP/Director of Security
    3. Head of AI Safety and Security
    4. Senior security researchers
    5. Board members with security expertise
    
    Include their:
    - Full name and title
    - Background and previous roles
    - LinkedIn profile if available
    - Key responsibilities
    - Notable security initiatives they've led
    
    Provide response as JSON:
    {{
        "security_staff": [
            {{
                "name": "Full Name",
                "title": "Official Title",
                "description": "Background and responsibilities",
                "previous_roles": ["Previous positions"],
                "linkedin": "LinkedIn URL if available",
                "initiatives": ["Key security initiatives"],
                "sources": ["URL1", "URL2"]
            }}
        ]
    }}
    """
    
    try:
        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=2048,
            messages=[{"role": "user", "content": query_prompt}],
            tools=[{
                "type": "web_search_20250305",
                "name": "web_search",
                "max_uses": 5
            }]
        )
        
        for content_block in response.content:
            if content_block.type == "text":
                result = parse_json_from_response(content_block.text)
                if result:
                    return result
        
        return {"security_staff": []}
        
    except Exception as e:
        print(f"Error searching security personnel for {ai_lab}: {e}", file=sys.stderr)
        return {"security_staff": []}

def search_infrastructure_relationships(ai_lab: str) -> Dict:
    """Search for cloud infrastructure and datacenter relationships."""
    query_prompt = f"""
    Search for detailed information about {ai_lab}'s infrastructure partnerships:
    1. Cloud service providers (AWS, Azure, GCP, etc.)
    2. Colocation facilities used
    3. Private datacenter locations
    4. Power infrastructure partners
    5. Network connectivity providers
    6. Hardware suppliers (especially AI chips)
    
    Find specific details about:
    - Contract announcements
    - Datacenter locations and sizes
    - Power requirements (MW/GW scale)
    - Cooling and power infrastructure vendors
    - Special security requirements (SCIF, air-gapped facilities)
    
    Provide response as JSON:
    {{
        "infrastructure": {{
            "cloud_providers": [
                {{
                    "name": "Provider name",
                    "relationship": "Description of partnership",
                    "services": ["Specific services used"],
                    "scale": "Size/scale if known",
                    "sources": ["URLs"]
                }}
            ],
            "datacenters": [
                {{
                    "location": "City, State/Country",
                    "size": "MW or sq ft",
                    "contractor": "Who built it",
                    "special_features": ["SCIF", "Air-gapped", etc],
                    "sources": ["URLs"]
                }}
            ],
            "power_cooling": [
                {{
                    "vendor": "Company name",
                    "services": "What they provide",
                    "projects": ["Specific projects"],
                    "sources": ["URLs"]
                }}
            ]
        }}
    }}
    """
    
    try:
        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=2048,
            messages=[{"role": "user", "content": query_prompt}],
            tools=[{
                "type": "web_search_20250305",
                "name": "web_search",
                "max_uses": 5
            }]
        )
        
        for content_block in response.content:
            if content_block.type == "text":
                result = parse_json_from_response(content_block.text)
                if result:
                    return result
        
        return {"infrastructure": {"cloud_providers": [], "datacenters": [], "power_cooling": []}}
        
    except Exception as e:
        print(f"Error searching infrastructure for {ai_lab}: {e}", file=sys.stderr)
        return {"infrastructure": {"cloud_providers": [], "datacenters": [], "power_cooling": []}}

def search_hidden_relationships() -> Dict:
    """Search for less obvious relationships and contractors in the AI infrastructure space."""
    query_prompt = """
    Search for lesser-known contractors and relationships in AI datacenter construction:
    1. Specialized SCIF contractors working on AI facilities
    2. Security system integrators for AI labs
    3. Specialized cooling vendors for high-density AI compute
    4. Fiber optic and network infrastructure contractors
    5. Environmental control and monitoring vendors
    6. Physical security contractors (guards, access control)
    7. Smaller regional contractors working on AI projects
    
    Look for:
    - Government contractors now working with AI labs
    - Military/defense contractors building secure facilities
    - Specialized engineering firms
    - Recent contract awards not widely publicized
    
    Provide response as JSON:
    {{
        "specialized_contractors": [
            {{
                "name": "Company name",
                "specialty": "What they specialize in",
                "ai_projects": ["Known AI lab projects"],
                "background": "Company background",
                "certifications": ["Security clearances, certifications"],
                "url": "Website",
                "sources": ["URLs"]
            }}
        ]
    }}
    """
    
    try:
        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=2048,
            messages=[{"role": "user", "content": query_prompt}],
            tools=[{
                "type": "web_search_20250305",
                "name": "web_search",
                "max_uses": 5
            }]
        )
        
        for content_block in response.content:
            if content_block.type == "text":
                result = parse_json_from_response(content_block.text)
                if result:
                    return result
        
        return {"specialized_contractors": []}
        
    except Exception as e:
        print(f"Error searching hidden relationships: {e}", file=sys.stderr)
        return {"specialized_contractors": []}

def build_network_data(all_data: Dict) -> Tuple[List[Dict], List[Dict]]:
    """Convert collected data into nodes and links for the network visualization."""
    nodes = []
    links = []
    node_ids = set()
    
    # Add SL5 core node
    nodes.append(create_node(
        "sl5-core",
        "SL5 Project",
        "core",
        "Security Level 5 Initiative - Advanced AI infrastructure security project",
        40,
        "",
        [],
        [{"text": "RAND Report: Securing AI Model Weights", "url": "https://www.rand.org/pubs/research_reports/RRA2977-1.html"}]
    ))
    node_ids.add("sl5-core")
    
    # Process AI labs and their data
    for lab_name, lab_data in all_data.items():
        # Create AI lab node
        lab_id = lab_name.lower().replace(" ", "-").replace(".", "")
        if lab_id not in node_ids:
            nodes.append(create_node(
                lab_id,
                lab_name,
                "ai_labs",
                f"Major AI research lab and model developer",
                40,
                "",
                [],
                []
            ))
            node_ids.add(lab_id)
            links.append(create_link("sl5-core", lab_id, 5))
        
        # Add contractors
        if "contractors" in lab_data:
            for contractor in lab_data["contractors"]:
                contractor_id = contractor["name"].lower().replace(" ", "-").replace(".", "")
                if contractor_id not in node_ids:
                    sources = [{"text": f"Source {i+1}", "url": url} 
                              for i, url in enumerate(contractor.get("sources", []))]
                    
                    nodes.append(create_node(
                        contractor_id,
                        contractor["name"],
                        "contractors",
                        contractor.get("description", ""),
                        25,
                        contractor.get("url", ""),
                        contractor.get("projects", []),
                        sources
                    ))
                    node_ids.add(contractor_id)
                
                links.append(create_link(lab_id, contractor_id, 4))
        
        # Add security personnel
        if "security_staff" in lab_data:
            for person in lab_data["security_staff"]:
                person_id = person["name"].lower().replace(" ", "-")
                if person_id not in node_ids:
                    sources = [{"text": f"Source {i+1}", "url": url} 
                              for i, url in enumerate(person.get("sources", []))]
                    
                    nodes.append(create_node(
                        person_id,
                        person["name"],
                        "security_personnel",
                        f"{person.get('title', '')} - {person.get('description', '')}",
                        20,
                        person.get("linkedin", ""),
                        person.get("initiatives", []),
                        sources
                    ))
                    node_ids.add(person_id)
                
                links.append(create_link(lab_id, person_id, 4))
        
        # Add infrastructure relationships
        if "infrastructure" in lab_data:
            infra = lab_data["infrastructure"]
            
            # Cloud providers
            for provider in infra.get("cloud_providers", []):
                provider_id = provider["name"].lower().replace(" ", "-")
                if provider_id not in node_ids:
                    sources = [{"text": f"Source {i+1}", "url": url} 
                              for i, url in enumerate(provider.get("sources", []))]
                    
                    nodes.append(create_node(
                        provider_id,
                        provider["name"],
                        "cloud_infrastructure",
                        provider.get("relationship", ""),
                        35,
                        "",
                        provider.get("services", []),
                        sources
                    ))
                    node_ids.add(provider_id)
                
                links.append(create_link(lab_id, provider_id, 5))
            
            # Power/cooling vendors
            for vendor in infra.get("power_cooling", []):
                vendor_id = vendor["vendor"].lower().replace(" ", "-")
                if vendor_id not in node_ids:
                    sources = [{"text": f"Source {i+1}", "url": url} 
                              for i, url in enumerate(vendor.get("sources", []))]
                    
                    nodes.append(create_node(
                        vendor_id,
                        vendor["vendor"],
                        "power_infrastructure",
                        vendor.get("services", ""),
                        25,
                        "",
                        vendor.get("projects", []),
                        sources
                    ))
                    node_ids.add(vendor_id)
                
                links.append(create_link(lab_id, vendor_id, 3))
    
    # Add specialized contractors
    if "specialized" in all_data:
        for contractor in all_data["specialized"]["specialized_contractors"]:
            contractor_id = contractor["name"].lower().replace(" ", "-")
            if contractor_id not in node_ids:
                sources = [{"text": f"Source {i+1}", "url": url} 
                          for i, url in enumerate(contractor.get("sources", []))]
                
                category = "security_contractors" if "security" in contractor.get("specialty", "").lower() else "contractors"
                
                nodes.append(create_node(
                    contractor_id,
                    contractor["name"],
                    category,
                    f"{contractor.get('specialty', '')} - {contractor.get('background', '')}",
                    20,
                    contractor.get("url", ""),
                    contractor.get("ai_projects", []),
                    sources
                ))
                node_ids.add(contractor_id)
                
                # Link to relevant AI labs
                for project in contractor.get("ai_projects", []):
                    for lab in AI_LABS:
                        if lab.lower() in project.lower():
                            lab_id = lab.lower().replace(" ", "-").replace(".", "")
                            links.append(create_link(lab_id, contractor_id, 3))
                            break
    
    return nodes, links

def main():
    parser = argparse.ArgumentParser(description="Gather SL5 stakeholder network data using Claude API")
    parser.add_argument("--limit", type=int, help="Limit number of AI labs to process")
    parser.add_argument("--output", default=OUTPUT_FILE, help="Output JSON file path")
    parser.add_argument("--skip-hidden", action="store_true", help="Skip searching for hidden relationships")
    args = parser.parse_args()
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    
    print(f"Starting SL5 stakeholder data collection for {len(AI_LABS)} AI labs...")
    print(f"Output will be saved to: {args.output}")
    
    all_data = {}
    labs_to_process = AI_LABS[:args.limit] if args.limit else AI_LABS
    
    # Collect data for each AI lab
    for i, lab in enumerate(labs_to_process):
        print(f"\n[{i+1}/{len(labs_to_process)}] Processing {lab}...")
        lab_data = {}
        
        # Search for contractors
        print(f"  - Searching for datacenter contractors...")
        contractors_data = search_datacenter_contractors(lab)
        if contractors_data.get("contractors"):
            lab_data["contractors"] = contractors_data["contractors"]
            print(f"    Found {len(contractors_data['contractors'])} contractors")
        time.sleep(2)  # Rate limiting
        
        # Search for security personnel
        print(f"  - Searching for security personnel...")
        security_data = search_security_personnel(lab)
        if security_data.get("security_staff"):
            lab_data["security_staff"] = security_data["security_staff"]
            print(f"    Found {len(security_data['security_staff'])} security staff")
        time.sleep(2)
        
        # Search for infrastructure relationships
        print(f"  - Searching for infrastructure partnerships...")
        infra_data = search_infrastructure_relationships(lab)
        if infra_data.get("infrastructure"):
            lab_data["infrastructure"] = infra_data["infrastructure"]
            print(f"    Found {len(infra_data['infrastructure'].get('cloud_providers', []))} cloud providers")
            print(f"    Found {len(infra_data['infrastructure'].get('datacenters', []))} datacenters")
            print(f"    Found {len(infra_data['infrastructure'].get('power_cooling', []))} power/cooling vendors")
        time.sleep(2)
        
        all_data[lab] = lab_data
    
    # Search for hidden/specialized relationships
    if not args.skip_hidden:
        print(f"\nSearching for specialized/hidden contractors...")
        hidden_data = search_hidden_relationships()
        if hidden_data.get("specialized_contractors"):
            all_data["specialized"] = hidden_data
            print(f"  Found {len(hidden_data['specialized_contractors'])} specialized contractors")
    
    # Build network visualization data
    print("\nBuilding network visualization data...")
    nodes, links = build_network_data(all_data)
    
    # Create final output
    output_data = {
        "nodes": nodes,
        "links": links,
        "citation": f"Data compiled from public sources via web search on {datetime.now().strftime('%Y-%m-%d')}. " +
                   "Information gathered using Claude AI with web search capabilities.",
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "ai_labs_searched": labs_to_process,
            "total_nodes": len(nodes),
            "total_links": len(links),
            "node_categories": list(set(node["category"] for node in nodes))
        }
    }
    
    # Save to file
    with open(args.output, "w") as f:
        json.dump(output_data, f, indent=2)
    
    print(f"\n✓ Data collection complete!")
    print(f"  - Total nodes: {len(nodes)}")
    print(f"  - Total links: {len(links)}")
    print(f"  - Output saved to: {args.output}")
    
    # Print category breakdown
    category_counts = {}
    for node in nodes:
        cat = node["category"]
        category_counts[cat] = category_counts.get(cat, 0) + 1
    
    print("\nNode breakdown by category:")
    for cat, count in sorted(category_counts.items()):
        print(f"  - {cat}: {count}")

if __name__ == "__main__":
    main()