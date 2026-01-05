"""
Neo4j graph database client for relationship mapping.
Manages knowledge graph for lateral thinking retrieval.
"""

from neo4j import GraphDatabase, AsyncGraphDatabase
from typing import Dict, List, Any, Optional
from app.config import get_settings

settings = get_settings()


class Neo4jClient:
    """Client for Neo4j knowledge graph operations."""
    
    def __init__(self):
        self.driver = GraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password)
        )
    
    def close(self):
        """Close the driver connection."""
        self.driver.close()
    
    def create_constraints(self):
        """Create uniqueness constraints and indexes."""
        with self.driver.session() as session:
            # Uniqueness constraints
            session.run("CREATE CONSTRAINT person_name IF NOT EXISTS FOR (p:Person) REQUIRE p.name IS UNIQUE")
            session.run("CREATE CONSTRAINT project_name IF NOT EXISTS FOR (p:Project) REQUIRE p.name IS UNIQUE")
            session.run("CREATE CONSTRAINT concept_name IF NOT EXISTS FOR (c:Concept) REQUIRE c.name IS UNIQUE")
            
            # Indexes for performance
            session.run("CREATE INDEX person_created IF NOT EXISTS FOR (p:Person) ON (p.created)")
            session.run("CREATE INDEX relationship_timestamp IF NOT EXISTS FOR ()-[r:RELATES_TO]-() ON (r.timestamp)")
    
    def create_or_update_node(
        self, 
        label: str, 
        name: str, 
        properties: Dict[str, Any]
    ) -> Dict:
        """Create a node if it doesn't exist, update if it does."""
        with self.driver.session() as session:
            result = session.run(  # type: ignore[arg-type]
                f"""
                MERGE (n:{label} {{name: $name}})
                ON CREATE SET 
                    n.created = timestamp(),
                    n.properties = $properties
                ON MATCH SET 
                    n.properties = $properties,
                    n.last_updated = timestamp()
                RETURN n
                """,
                name=name,
                properties=properties
            )
            record = result.single()
            return record["n"] if record else {}
    
    def create_relationship(
        self,
        from_label: str,
        from_name: str,
        to_label: str,
        to_name: str,
        relationship_type: str,
        properties: Optional[Dict[str, Any]] = None
    ):
        """Create or update a relationship between two nodes."""
        properties = properties or {}
        
        with self.driver.session() as session:
            session.run(  # type: ignore[arg-type]
                f"""
                MATCH (a:{from_label} {{name: $from_name}})
                MATCH (b:{to_label} {{name: $to_name}})
                MERGE (a)-[r:{relationship_type}]->(b)
                ON CREATE SET 
                    r.created = timestamp(),
                    r.properties = $properties
                ON MATCH SET 
                    r.last_seen = timestamp(),
                    r.properties = $properties
                RETURN r
                """,
                from_name=from_name,
                to_name=to_name,
                properties=properties
            )
    
    def traverse_graph(
        self,
        start_node: str,
        max_depth: int = 3,
        relationship_types: Optional[List[str]] = None
    ) -> List[Dict]:
        """Traverse the graph from a starting node."""
        rel_filter = ""
        if relationship_types:
            rel_types = "|".join(relationship_types)
            rel_filter = f":{rel_types}"
        
        with self.driver.session() as session:
            result = session.run(  # type: ignore[arg-type]
                f"""
                MATCH path = (start {{name: $start_node}})-[r{rel_filter}*1..{max_depth}]-(connected)
                RETURN connected, r, length(path) as depth
                ORDER BY depth
                """,
                start_node=start_node
            )
            
            return [
                {
                    "node": record["connected"],
                    "relationships": record["r"],
                    "depth": record["depth"]
                }
                for record in result
            ]
    
    def find_shortest_path(self, from_node: str, to_node: str) -> Optional[Dict]:
        """Find the shortest path between two nodes."""
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (start {name: $from_node}), (end {name: $to_node}),
                path = shortestPath((start)-[*]-(end))
                RETURN nodes(path) as nodes, relationships(path) as relationships
                """,
                from_node=from_node,
                to_node=to_node
            )
            
            record = result.single()
            if record:
                return {
                    "nodes": record["nodes"],
                    "relationships": record["relationships"]
                }
            return None
    
    def get_node_neighborhood(self, node_name: str, radius: int = 2) -> Dict:
        """Get all nodes within a certain radius of a target node."""
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (center {name: $node_name})
                CALL apoc.path.subgraphAll(center, {
                    maxLevel: $radius
                })
                YIELD nodes, relationships
                RETURN nodes, relationships
                """,
                node_name=node_name,
                radius=radius
            )
            
            record = result.single()
            if record:
                return {
                    "nodes": record["nodes"],
                    "relationships": record["relationships"]
                }
            return {"nodes": [], "relationships": []}
    
    def export_graph_state(self) -> Dict:
        """Export the entire graph state for snapshotting."""
        with self.driver.session() as session:
            # Get all nodes
            nodes_result = session.run("MATCH (n) RETURN n")
            nodes = [record["n"] for record in nodes_result]
            
            # Get all relationships
            rels_result = session.run("MATCH ()-[r]->() RETURN r")
            relationships = [record["r"] for record in rels_result]
            
            return {
                "nodes": nodes,
                "relationships": relationships,
                "node_count": len(nodes),
                "relationship_count": len(relationships)
            }
    
    def clear_graph(self):
        """Clear all nodes and relationships (use with caution!)."""
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")


# Lazy initialization - only create when first accessed
_neo4j_client: Optional[Neo4jClient] = None


def get_neo4j_client() -> Neo4jClient:
    """Get or create the Neo4j client instance."""
    global _neo4j_client
    if _neo4j_client is None:
        _neo4j_client = Neo4jClient()
    return _neo4j_client


# Lazy wrapper for backward compatibility
class LazyNeo4jClient(Neo4jClient):  # type: ignore
    """Lazy wrapper for backward compatibility with existing code."""
    _instance: Optional[Neo4jClient] = None
    
    def __init__(self):
        # Don't call super().__init__() - lazy init
        pass
    
    def __getattr__(self, name):
        if self._instance is None:
            self._instance = get_neo4j_client()
        return getattr(self._instance, name)


neo4j_client = LazyNeo4jClient()
