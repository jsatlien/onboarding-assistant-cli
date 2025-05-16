#!/usr/bin/env python3
"""
Metadata Generator for Onboarding Assistant

This CLI tool scans source code files (.vue, .cs, .json) to extract contextual metadata
for the Onboarding Assistant. The metadata is output as structured JSON files that can
be used for RAG embedding.
"""

import os
import re
import json
import argparse
from typing import Dict, List, Optional, Any
import glob

# Define the structure for our metadata
class UiElement:
    def __init__(self, id: str, description: str):
        self.id = id
        self.description = description
    
    def to_dict(self) -> Dict[str, str]:
        return {
            "id": self.id,
            "description": self.description
        }

class RouteContext:
    def __init__(self, route: str, description: str):
        self.route = route
        self.description = description
        self.elements: List[UiElement] = []
        self.api_calls: List[str] = []
        self.dependencies: Optional[List[str]] = None
        self.user_actions: List[str] = []
    
    def add_element(self, element: UiElement) -> None:
        self.elements.append(element)
    
    def add_api_call(self, api_call: str) -> None:
        if api_call not in self.api_calls:
            self.api_calls.append(api_call)
    
    def add_dependency(self, dependency: str) -> None:
        if self.dependencies is None:
            self.dependencies = []
        if dependency not in self.dependencies:
            self.dependencies.append(dependency)
    
    def add_user_action(self, action: str) -> None:
        if action not in self.user_actions:
            self.user_actions.append(action)
    
    def to_dict(self) -> Dict[str, Any]:
        result = {
            "route": self.route,
            "description": self.description,
            "elements": [element.to_dict() for element in self.elements],
            "apiCalls": self.api_calls,
            "userActions": self.user_actions
        }
        if self.dependencies:
            result["dependencies"] = self.dependencies
        return result

class MetadataGenerator:
    def __init__(self, source_dir: str, output_dir: str):
        self.source_dir = os.path.abspath(source_dir)
        self.output_dir = os.path.abspath(output_dir)
        self.route_contexts: Dict[str, RouteContext] = {}
    
    def scan_files(self) -> None:
        """Scan all relevant files in the source directory."""
        print(f"Scanning files in {self.source_dir}...")
        
        # Scan Vue files
        vue_files = glob.glob(f"{self.source_dir}/**/*.vue", recursive=True)
        for file_path in vue_files:
            self._process_vue_file(file_path)
        
        # Scan C# files
        cs_files = glob.glob(f"{self.source_dir}/**/*.cs", recursive=True)
        for file_path in cs_files:
            self._process_cs_file(file_path)
        
        # Scan JSON files (for route definitions, etc.)
        json_files = glob.glob(f"{self.source_dir}/**/*.json", recursive=True)
        for file_path in json_files:
            self._process_json_file(file_path)
        
        print(f"Found metadata for {len(self.route_contexts)} routes")
    
    def _process_vue_file(self, file_path: str) -> None:
        """Extract metadata from a Vue file."""
        try:
            relative_path = os.path.relpath(file_path, self.source_dir)
            print(f"Processing Vue file: {relative_path}")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Try to determine the route from the file path or content
            route = self._extract_route_from_vue(file_path, content)
            if not route:
                print(f"  Could not determine route for {relative_path}, skipping")
                return
            
            # Create or get the route context
            if route not in self.route_contexts:
                # Try to extract a description from comments or component name
                description = self._extract_description_from_vue(content) or f"Page at {route}"
                self.route_contexts[route] = RouteContext(route, description)
            
            context = self.route_contexts[route]
            
            # Extract UI elements (look for id attributes, ref bindings, etc.)
            elements = self._extract_elements_from_vue(content)
            for element_id, description in elements.items():
                context.add_element(UiElement(element_id, description))
            
            # Extract API calls (look for axios calls, fetch, etc.)
            api_calls = self._extract_api_calls_from_vue(content)
            for api_call in api_calls:
                context.add_api_call(api_call)
            
            # Extract dependencies (imported components)
            dependencies = self._extract_dependencies_from_vue(content)
            for dependency in dependencies:
                context.add_dependency(dependency)
            
            # Extract user actions (from comments, method names, etc.)
            user_actions = self._extract_user_actions_from_vue(content)
            for action in user_actions:
                context.add_user_action(action)
            
        except Exception as e:
            print(f"  Error processing {file_path}: {str(e)}")
    
    def _process_cs_file(self, file_path: str) -> None:
        """Extract metadata from a C# file."""
        try:
            relative_path = os.path.relpath(file_path, self.source_dir)
            print(f"Processing C# file: {relative_path}")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # For C# files, we're primarily interested in API endpoints
            if 'Controller' in os.path.basename(file_path):
                api_routes = self._extract_api_routes_from_cs(content)
                
                # Associate API routes with frontend routes if possible
                for api_route in api_routes:
                    # This is a simplistic approach - in a real implementation,
                    # you would need a more sophisticated mapping between 
                    # API routes and frontend routes
                    route_parts = api_route.split('/')
                    if len(route_parts) > 2:
                        potential_route = f"/{route_parts[1]}"
                        if potential_route in self.route_contexts:
                            self.route_contexts[potential_route].add_api_call(api_route)
                        
                        # Also try with the second part
                        if len(route_parts) > 3:
                            potential_route = f"/{route_parts[1]}/{route_parts[2]}"
                            if potential_route in self.route_contexts:
                                self.route_contexts[potential_route].add_api_call(api_route)
            
        except Exception as e:
            print(f"  Error processing {file_path}: {str(e)}")
    
    def _process_json_file(self, file_path: str) -> None:
        """Extract metadata from a JSON file."""
        try:
            # Skip package.json, package-lock.json, etc.
            if os.path.basename(file_path) in ['package.json', 'package-lock.json', 'tsconfig.json']:
                return
            
            relative_path = os.path.relpath(file_path, self.source_dir)
            print(f"Processing JSON file: {relative_path}")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Look for route definitions, component metadata, etc.
            # This is highly dependent on the structure of your JSON files
            if isinstance(data, dict) and 'route' in data:
                route = data['route']
                if route not in self.route_contexts:
                    description = data.get('description', f"Page at {route}")
                    self.route_contexts[route] = RouteContext(route, description)
                
                context = self.route_contexts[route]
                
                # Extract elements
                if 'elements' in data and isinstance(data['elements'], list):
                    for element in data['elements']:
                        if isinstance(element, dict) and 'id' in element and 'description' in element:
                            context.add_element(UiElement(element['id'], element['description']))
                
                # Extract API calls
                if 'apiCalls' in data and isinstance(data['apiCalls'], list):
                    for api_call in data['apiCalls']:
                        if isinstance(api_call, str):
                            context.add_api_call(api_call)
                
                # Extract dependencies
                if 'dependencies' in data and isinstance(data['dependencies'], list):
                    for dependency in data['dependencies']:
                        if isinstance(dependency, str):
                            context.add_dependency(dependency)
                
                # Extract user actions
                if 'userActions' in data and isinstance(data['userActions'], list):
                    for action in data['userActions']:
                        if isinstance(action, str):
                            context.add_user_action(action)
            
        except Exception as e:
            print(f"  Error processing {file_path}: {str(e)}")
    
    def _extract_route_from_vue(self, file_path: str, content: str) -> Optional[str]:
        """Try to determine the route from a Vue file."""
        # Check for route definitions in the script section
        route_pattern = r"path:\s*['\"]([^'\"]+)['\"]"
        matches = re.findall(route_pattern, content)
        if matches:
            return matches[0]
        
        # Try to infer from file path
        # This is a simplistic approach and would need to be adapted to your project structure
        file_name = os.path.basename(file_path)
        if file_name.lower() == 'index.vue':
            # Get the parent directory name
            parent_dir = os.path.basename(os.path.dirname(file_path))
            if parent_dir.lower() != 'src' and parent_dir.lower() != 'pages':
                return f"/{parent_dir}"
        else:
            # Remove the .vue extension
            base_name = os.path.splitext(file_name)[0]
            if base_name.lower() != 'app':
                return f"/{base_name.lower()}"
        
        return None
    
    def _extract_description_from_vue(self, content: str) -> Optional[str]:
        """Extract a description from a Vue file."""
        # Look for a comment that describes the component
        description_pattern = r"<!--\s*(.+?)\s*-->"
        matches = re.findall(description_pattern, content)
        if matches:
            return matches[0]
        
        # Look for a description in the script section
        script_description_pattern = r"\/\*\*\s*\n\s*\*\s*(.+?)\s*\n"
        matches = re.findall(script_description_pattern, content)
        if matches:
            return matches[0]
        
        return None
    
    def _extract_elements_from_vue(self, content: str) -> Dict[str, str]:
        """Extract UI elements from a Vue file."""
        elements = {}
        
        # Look for elements with id attributes
        id_pattern = r"id=['\"]([^'\"]+)['\"]"
        id_matches = re.findall(id_pattern, content)
        
        # Look for elements with ref bindings
        ref_pattern = r"ref=['\"]([^'\"]+)['\"]"
        ref_matches = re.findall(ref_pattern, content)
        
        # Combine the matches
        element_ids = set(id_matches + ref_matches)
        
        # Try to find descriptions for each element
        for element_id in element_ids:
            # Look for comments near the element
            element_pattern = r"<!--\s*(.+?)\s*-->\s*<[^>]*id=['\"]" + re.escape(element_id) + r"['\"]"
            matches = re.findall(element_pattern, content)
            if matches:
                elements[element_id] = matches[0]
            else:
                # If no comment found, use a generic description
                elements[element_id] = f"UI element with ID {element_id}"
        
        return elements
    
    def _extract_api_calls_from_vue(self, content: str) -> List[str]:
        """Extract API calls from a Vue file."""
        api_calls = []
        
        # Look for axios calls
        axios_pattern = r"axios\.(get|post|put|delete)\(['\"]([^'\"]+)['\"]"
        axios_matches = re.findall(axios_pattern, content)
        for method, url in axios_matches:
            if url.startswith('/api/'):
                api_calls.append(f"{method.upper()} {url}")
        
        # Look for fetch calls
        fetch_pattern = r"fetch\(['\"]([^'\"]+)['\"]"
        fetch_matches = re.findall(fetch_pattern, content)
        for url in fetch_matches:
            if url.startswith('/api/'):
                api_calls.append(f"GET {url}")  # Assuming GET for simplicity
        
        return api_calls
    
    def _extract_dependencies_from_vue(self, content: str) -> List[str]:
        """Extract dependencies from a Vue file."""
        dependencies = []
        
        # Look for imported components
        import_pattern = r"import\s+(\w+)\s+from"
        import_matches = re.findall(import_pattern, content)
        
        # Look for components defined in the components section
        components_pattern = r"components:\s*{([^}]+)}"
        components_matches = re.findall(components_pattern, content)
        if components_matches:
            components_str = components_matches[0]
            component_names = re.findall(r"(\w+)", components_str)
            dependencies.extend(component_names)
        
        return list(set(import_matches))
    
    def _extract_user_actions_from_vue(self, content: str) -> List[str]:
        """Extract user actions from a Vue file."""
        user_actions = []
        
        # Look for method names that suggest user actions
        method_pattern = r"methods:\s*{([^}]+)}"
        method_matches = re.findall(method_pattern, content)
        if method_matches:
            methods_str = method_matches[0]
            method_names = re.findall(r"(\w+)\s*\(", methods_str)
            
            # Filter for method names that suggest user actions
            action_prefixes = ['handle', 'on', 'toggle', 'submit', 'create', 'update', 'delete', 'view', 'show', 'hide']
            for method in method_names:
                for prefix in action_prefixes:
                    if method.lower().startswith(prefix.lower()):
                        # Convert camelCase to readable text
                        action = re.sub(r'([A-Z])', r' \1', method)
                        action = action.replace(prefix, '', 1).strip()
                        if action:
                            user_actions.append(action)
                        break
        
        return user_actions
    
    def _extract_api_routes_from_cs(self, content: str) -> List[str]:
        """Extract API routes from a C# controller file."""
        api_routes = []
        
        # Look for route attributes
        route_pattern = r"\[Route\(['\"]([^'\"]+)['\"]\)\]"
        route_matches = re.findall(route_pattern, content)
        
        # Look for HTTP method attributes with routes
        http_method_pattern = r"\[(HttpGet|HttpPost|HttpPut|HttpDelete)(?:\(['\"]([^'\"]+)['\"]\))?\]"
        http_method_matches = re.findall(http_method_pattern, content)
        
        # Process route matches
        for route in route_matches:
            if not route.startswith('/'):
                route = '/' + route
            
            # Check if this is an API route
            if route.startswith('/api/'):
                api_routes.append(f"GET {route}")  # Default to GET for base routes
        
        # Process HTTP method matches
        for method, sub_route in http_method_matches:
            for base_route in route_matches:
                if not base_route.startswith('/'):
                    base_route = '/' + base_route
                
                full_route = base_route
                if sub_route:
                    if not sub_route.startswith('/'):
                        full_route += '/' + sub_route
                    else:
                        full_route += sub_route
                
                # Check if this is an API route
                if full_route.startswith('/api/'):
                    api_routes.append(f"{method.replace('Http', '')} {full_route}")
        
        return api_routes
    
    def generate_output(self) -> None:
        """Generate JSON output files for each route context."""
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        
        print(f"Generating output files in {self.output_dir}...")
        
        for route, context in self.route_contexts.items():
            # Create a safe filename from the route
            safe_route = route.replace('/', '-').lstrip('-')
            if not safe_route:
                safe_route = 'index'
            
            output_path = os.path.join(self.output_dir, f"{safe_route}.json")
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(context.to_dict(), f, indent=2)
            
            print(f"  Generated {output_path}")

def main():
    parser = argparse.ArgumentParser(description='Generate metadata for Onboarding Assistant')
    parser.add_argument('source_dir', help='Source directory to scan')
    parser.add_argument('--output-dir', '-o', default='./output', help='Output directory for metadata files')
    
    args = parser.parse_args()
    
    generator = MetadataGenerator(args.source_dir, args.output_dir)
    generator.scan_files()
    generator.generate_output()
    
    print("Metadata generation complete!")

if __name__ == '__main__':
    main()
