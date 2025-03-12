from flask import Blueprint, jsonify, request
from app import db
from app.models import WeeklyPlan, MealSlot, Recipe
from datetime import datetime
import logging

meal_planner_routes = Blueprint('meal_planner_routes', __name__)

# Configure logging
logger = logging.getLogger(__name__)




@meal_planner_routes.route('/api/weekly_plan', methods=['POST'])
def save_weekly_plan():
    """Save a new weekly meal plan."""
    try:
        # Parse request data
        data = request.json
        name = data.get('name', f"My Weekly Plan ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})")
        meals = data.get('meals', [])

        if not meals:
            return jsonify({"error": "No meals provided"}), 400

        # Create and save the weekly plan
        weekly_plan = WeeklyPlan(name=name, created_at=datetime.utcnow())
        db.session.add(weekly_plan)

        # Flush to assign an ID to the weekly_plan
        db.session.flush()

        # Associate meals with the weekly plan
        for meal in meals:
            meal_slot = MealSlot(
                weekly_plan_id=weekly_plan.id,  # Now `weekly_plan.id` is available
                day=meal['day'],
                meal_type=meal['meal_type'],
                recipe_id=meal.get('recipe_id')
            )
            db.session.add(meal_slot)

        # Commit all changes to the database
        db.session.commit()

        return jsonify({"message": "Weekly plan saved successfully", "id": weekly_plan.id}), 201

    except Exception as e:
        logger.error(f"Error saving weekly plan: {e}")
        return jsonify({"error": "An error occurred while saving the plan"}), 500
    
@meal_planner_routes.route('/api/weekly_plan_list', methods=['GET'])
def list_weekly_plans():
    """List all weekly plans."""
    try:
        plans = WeeklyPlan.query.all()
        return jsonify([{"id": plan.id, "name": plan.name} for plan in plans]), 200
    except Exception as e:
        logger.error(f"Error fetching weekly plans: {e}")
        return jsonify({"error": "An error occurred while fetching weekly plans."}), 500
    
@meal_planner_routes.route('/api/weekly_plan/<int:plan_id>', methods=['GET'])
def get_weekly_plan(plan_id):
    """Get details for a specific weekly plan."""
    try:
        plan = WeeklyPlan.query.get_or_404(plan_id)
        
        # Get meal slots
        meal_slots = MealSlot.query.filter_by(weekly_plan_id=plan_id).all()
        
        # Calculate ingredient count safely
        try:
            ingredient_count = plan.ingredient_count
        except Exception as e:
            logger.error(f"Error calculating ingredient count: {e}")
            ingredient_count = 0
        
        return jsonify({
            'id': plan.id,
            'name': plan.name,
            'created_at': plan.created_at.isoformat() if plan.created_at else None,
            'updated_at': plan.updated_at.isoformat() if plan.updated_at else None,
            'meals': [meal.to_dict() for meal in meal_slots],
            'ingredient_count': ingredient_count
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching weekly plan {plan_id}: {e}")
        return jsonify({"error": str(e)}), 500

@meal_planner_routes.route('/api/weekly_plan/<int:plan_id>', methods=['DELETE'])
def delete_weekly_plan(plan_id):
    """Delete a weekly plan."""
    try:
        plan = WeeklyPlan.query.get_or_404(plan_id)
        
        # Delete will cascade to meal slots due to relationship definition
        db.session.delete(plan)
        db.session.commit()
        
        return jsonify({"message": "Weekly plan deleted successfully"}), 200
        
    except Exception as e:
        logger.error(f"Error deleting weekly plan {plan_id}: {e}")
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@meal_planner_routes.route('/api/weekly_plan/<int:plan_id>/update', methods=['PUT'])
def update_weekly_plan(plan_id):
    """Update an existing weekly plan."""
    try:
        plan = WeeklyPlan.query.get_or_404(plan_id)
        
        data = request.json
        if not data:
            return jsonify({"error": "No data provided"}), 400
            
        # Update plan name if provided
        if 'name' in data:
            plan.name = data['name']
            
        # Update meals if provided
        if 'meals' in data:
            # Delete existing meal slots
            MealSlot.query.filter_by(weekly_plan_id=plan_id).delete()
            
            # Add new meal slots
            for meal in data['meals']:
                meal_slot = MealSlot(
                    weekly_plan_id=plan_id,
                    day=meal['day'],
                    meal_type=meal['meal_type'],
                    recipe_id=meal.get('recipe_id')
                )
                db.session.add(meal_slot)
                
        # Update timestamp
        plan.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            "message": "Weekly plan updated successfully",
            "id": plan.id
        }), 200
        
    except Exception as e:
        logger.error(f"Error updating weekly plan {plan_id}: {e}")
        db.session.rollback()
        return jsonify({"error": str(e)}), 500