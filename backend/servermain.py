from flask import Flask, request, jsonify
from opensearchpy import OpenSearch
from opensearchpy.exceptions import NotFoundError
from flask_cors import CORS
import traceback

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "http://localhost:3000"}})

# Configure OpenSearch client
client = OpenSearch(
    hosts=[{'host': 'localhost', 'port': 9200}],
    http_compress=True
)

@app.route('/search', methods=['GET'])
def search():
    try:
        query = request.args.get('q', '')  # Search term
        min_calories = request.args.get('min_calories', None)  # Min calories
        max_calories = request.args.get('max_calories', None)  # Max calories
        min_rating = request.args.get('min_rating', None)  # Min rating
        max_rating = request.args.get('max_rating', None)  # Max rating
        min_protein = request.args.get('min_protein', None)  # Min protein
        max_protein = request.args.get('max_protein', None)  # Max protein
        min_fat = request.args.get('min_fat', None)  # Min fat
        max_fat = request.args.get('max_fat', None)  # Max fat
        min_sodium = request.args.get('min_sodium', None)  # Min sodium
        max_sodium = request.args.get('max_sodium', None)  # Max sodium
        tags = request.args.get('tags', '')  # Tags
        ingredients = request.args.get('ingredients', '')  # Ingredients
        category = request.args.get('category', '')  # Category filter
        page = int(request.args.get('page', 1))  # Pagination page
        size = int(request.args.get('size', 10))  # Results per page

        # Split tags and ingredients if provided
        tags = [tag.strip('#') for tag in tags.split(',')] if tags else []
        ingredients = [ingredient.strip() for ingredient in ingredients.split(',')] if ingredients else []

        # Static list of non-ingredient fields
        non_ingredient_fields = ['title', 'calories', 'fat', 'sodium', 'rating', 'protein']

        # Step 1: Retrieve index mapping to identify all available fields
        index_mapping = client.indices.get_mapping(index="recipes")

        # Get all available fields in the index
        available_fields = index_mapping['recipes']['mappings']['properties'].keys()

        # Step 2: Identify ingredient fields by excluding non-ingredient fields and tags
        ingredient_fields = [field for field in available_fields if field not in non_ingredient_fields and not field.startswith('#')]

        # Step 3: Build the search query
        search_query = {
            "from": (page - 1) * size,
            "size": size,
            "query": {
                "bool": {
                    "must": [],
                    "filter": []
                }
            }
        }

        # Add search term if provided
        if query:
            search_query['query']['bool']['must'].append({"match": {"title": query}})

        # Add category filter if provided
        if category:
            search_query['query']['bool']['filter'].append({"match": {"categories": category}})
        # if category:
        #     search_query['query']['bool']['filter'].append({
        #         "term": {
        #             "categories.keyword": category
        #         }
        #     })

        # Add calorie filter if provided
        if min_calories or max_calories:
            search_query['query']['bool']['filter'].append({
                "range": {
                    "calories": {
                        "gte": int(min_calories or 0),
                        "lte": int(max_calories or 10000)
                    }
                }
            })

        # Add rating filter if provided
        if min_rating or max_rating:
            search_query['query']['bool']['filter'].append({
                "range": {
                    "rating": {
                        "gte": float(min_rating or 0),
                        "lte": float(max_rating or 5)
                    }
                }
            })

        # Add fat filter if provided
        if min_fat or max_fat:
            search_query['query']['bool']['filter'].append({
                "range": {
                    "fat": {
                        "gte": float(min_fat or 0),
                        "lte": float(max_fat or 100)
                    }
                }
            })

        # Add sodium filter if provided
        if min_sodium or max_sodium:
            search_query['query']['bool']['filter'].append({
                "range": {
                    "sodium": {
                        "gte": float(min_sodium or 0),
                        "lte": float(max_sodium or 10000)
                    }
                }
            })

        # Add protein filter if provided
        if min_protein or max_protein:
            search_query['query']['bool']['filter'].append({
                "range": {
                    "protein": {
                        "gte": float(min_protein or 0),
                        "lte": float(max_protein or 100)
                    }
                }
            })

        # Add tags filter if provided
        for tag in tags:
            search_query['query']['bool']['filter'].append({
                "term": {f"#{tag}": 1}
            })

        # Add ingredients filter for dynamically identified ingredient fields
        if ingredients:
            ingredient_conditions = []
            for ingredient in ingredients:
                # Match query for ingredients field
                ingredient_conditions.append({"match": {"ingredients": ingredient}})
            search_query['query']['bool']['must'].extend(ingredient_conditions)

        # Execute the search query
        response = client.search(
            body=search_query,
            index="recipes"
        )

        return jsonify(response['hits']['hits'])

    except NotFoundError as e:
        return jsonify({"error": "Index not found", "details": str(e)}), 404
    except Exception as e:
        print("An error occurred: ", str(e))
        print(traceback.format_exc())
        return jsonify({"error": "An error occurred", "details": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
