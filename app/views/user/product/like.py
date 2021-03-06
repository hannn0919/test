from flask import redirect, render_template, url_for, abort
from flask.views import MethodView
from flask_login import current_user, login_required

from app.models.product import Product
from app.models.information import Information


class LikeView(MethodView):
    def get(self):
        products = Information.objects(user_id=current_user.id).first().like

        return render_template('user/product/like.html', products=products)
    def post(self):
    	pass