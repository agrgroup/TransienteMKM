import re
from collections import defaultdict
import heapq
import graphviz
import streamlit as st


def parse_dot_file(file_path):
    with open(file_path, 'r') as file:
        dot_content = file.read()
    
    species_pattern = r'"([^"]+)"(?:\[.*?label="([^"\\]+)\\n([^"]+)".*?\])?;'
    species_matches = re.findall(species_pattern, dot_content)
    
    intermediates = []
    reactants = []
    products = []
    
    for match in species_matches:
        species = match[0]
        value = float(match[2]) if len(match) > 2 else None
        
        if '*' in species:
            intermediates.append(species)
        elif value is not None:
            if value != 0:
                reactants.append(species)
            else:
                products.append(species)
    
    return intermediates, reactants, products

def extract_reactions(file_path):
    with open(file_path, 'r') as file:
        dot_content = file.read()
    
    reaction_pattern = r'"([^"]+)"\s*->\s*"([^"]+)"\s*\[label="([^"]+)"'
    reaction_matches = re.findall(reaction_pattern, dot_content)
    
    graph = defaultdict(list)
    for match in reaction_matches:
        reactant, product, rate_info = match
        forward_rate, backward_rate = extract_rates(rate_info)
        rate = forward_rate - backward_rate
        graph[reactant].append((product, rate))
        graph[product].append((reactant, -rate))  # Add reverse reaction
    
    return graph

def extract_rates(rate_info):
    rate_pattern = r'([\d.e+-]+)\s*\[([\d.e+-]+)\s*\|\s*([\d.e+-]+)\s*\]'
    match = re.search(rate_pattern, rate_info)
    if match:
        return float(match.group(2)), float(match.group(3))
    return 0, 0

def find_rds(graph, start, end):
    pq = [(0, start, [])]
    visited = set()
    
    while pq:
        (cost, node, path) = heapq.heappop(pq)
        
        if node not in visited:
            visited.add(node)
            path = path + [node]
            
            if node == end:
                # Find RDS (step with lowest rate)
                rds = min(zip(path[:-1], path[1:]), key=lambda x: abs(graph[x[0]][graph[x[0]].index((x[1], next(rate for n, rate in graph[x[0]] if n == x[1])))][1]))
                return path, rds
            
            for neighbor, rate in graph[node]:
                if neighbor not in visited:
                    heapq.heappush(pq, (cost - rate, neighbor, path))
    
    return None, None

def create_reaction_network_visualization(dot_file=None, dot_content=None):
    if dot_file:
        # Read content from the provided .dot file
        with open(dot_file, 'r') as f:
            dot_content = f.read()
    
    if dot_content is None:
        st.error("No content provided.")
        return None
    
    # Create a new Graphviz object
    dot = graphviz.Digraph(comment='Reaction Network')
    dot.attr(rankdir='LR', size='12,8')
    
    # Regular expressions to match nodes and edges
    node_pattern = r'"([^"]+)"(?:\[.*?label="([^"\\]+)\\n([^"]+)".*?\])?;'
    edge_pattern = r'"([^"]+)"\s*->\s*"([^"]+)"\s*\[label="([^"]+)"'
    
    # Process nodes
    for match in re.finditer(node_pattern, dot_content):
        species = match.group(1)
        label = f"{species}\n{match.group(3)}" if match.group(3) else species
        
        if '*' in species:  # Intermediate
            dot.node(species, label, shape='box', style='filled', fillcolor='lightblue')
        elif match.group(3) and float(match.group(3)) != 0:  # Reactant
            dot.node(species, label, shape='ellipse', style='filled', fillcolor='lightgreen')
        else:  # Product
            dot.node(species, label, shape='ellipse', style='filled', fillcolor='lightyellow')
    
    # Process edges
    for match in re.finditer(edge_pattern, dot_content):
        source, target, rate_info = match.groups()
        
        # Extract forward and backward rates
        rate_match = re.search(r'([\d.e+-]+)\s*\[([\d.e+-]+)\s*\|\s*([\d.e+-]+)\s*\]', rate_info)
        if rate_match:
            forward_rate = float(rate_match.group(2))
            backward_rate = float(rate_match.group(3))
            
            # Create a bidirectional edge with both rates
            label = f"→ {forward_rate:.2e}\n← {backward_rate:.2e}"
            dot.edge(source, target, label=label, dir='both', arrowhead='normal', arrowtail='normal')
        else:
            # If rate information is not in the expected format, add a default edge
            dot.edge(source, target, label=rate_info, dir='both', arrowhead='normal', arrowtail='normal')
    
    return dot