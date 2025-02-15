from flask import Flask,request,redirect,render_template,jsonify,session,url_for
import pymongo
from flask_session import Session
import models

app=Flask(__name__)

app.secret_key = 'your secret key'
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

server = pymongo.MongoClient("mongodb://localhost:27017")
db = server['grocery']
users_tb = db['users']
products_tb = db['products']
carts_tb = db['carts']
orders_tb = db['orders']

@app.route('/',methods=['GET','POST'])
def index():
    msg = ""
    session['shop_name'] = 'null'
    session['role']='null'
    if request.method == 'POST':
        data = request.form
        name = data['username']
        password = data['password']
        user = users_tb.find_one({'Name':name, 'Password':password},{'_id':0})
        if user:
            session['id'] = user['Id']
            session['name'] = user['Name']
            session['role']=user['Role']
            if session['role'] == 'seller':
                session['shop_name'] = user['Shop']
            return redirect(url_for('dashboard'))
        else:
            msg = "The username or password is Incorrect"
    return render_template('home.html',msg=msg)

@app.route('/dashboard')
def dashboard():
    if session['role'] == 'seller':
        products = list(products_tb.find({'Shop_Name': {'$ne': session['shop_name']}},{'_id':0}))
    else:    
        products = list(products_tb.find({},{'_id':0}))
    return render_template('/dashboard.html',products=products)

@app.route('/register',methods=['POST','GET'])
def register():
    session['role']='null'
    if request.method == 'POST':
        data = request.form
        name = data['username']
        password = data['userpassword']
        mobile = data['usernumber']
        email = data['useremail']
        users_tb.insert_one({'Name':name, 'Password':password, 'Phone':mobile, 'Email':email, 'Role':'user'})
        return redirect(url_for('index'))
    return render_template('register.html')

@app.route('/view_products',methods=['GET','POST'])
def view_products():
    products = list(products_tb.find({'Shop_Name':session['shop_name']},{'_id':0}))
    return render_template('seller_products.html',products=products)

@app.post('/add_product_to_shop')
def add_product_to_shop():
    data = request.form
    product_name = data['product_name']
    product_price = data['product_price']
    product_quantity = data['product_quantity']
    product_url = data['product_url']
    shop_name = data['shop_name']
    latest_id = products_tb.find_one(sort=[('Product_Id', -1)])
    id = int(latest_id['Product_Id']) + 1 if latest_id else 1
    products_tb.insert_one({'Product_Name':product_name,'Product_Price':product_price,'Product_Quantity':product_quantity, 'Product_URL':product_url, 'Shop_Name':shop_name, 'Product_Id':id})
    return jsonify({'msg':"Ok da parama"})

@app.post('/add_to_cart')
def add_to_cart():
    data = request.form
    product_id = data['product_id']
    product_quantity = data['quantity']
    exist = carts_tb.find_one({'Id':session['id'],'Product_Id':int(product_id)})
    if exist:
        exist_quantity = exist['Product_Quantity']
        carts_tb.update_one({'Product_Id':int(product_id),'Id':session['id']},{ "$set": { "Product_Quantity": exist_quantity+int(product_quantity)} })
    else:
        carts_tb.insert_one({'Id':session['id'], 'Product_Id':int(product_id), 'Product_Quantity':int(product_quantity)})
    return jsonify({'msg':"Product Added to Cart"})

@app.route('/user_carts',methods=['GET','POST'])
def user_carts():
    total_price = 0
    carts = list(carts_tb.find(({'Id':session['id']})))
    for item in carts:
        cur_product = products_tb.find_one({'Product_Id':int(item['Product_Id'])},{'_id':0})
        if cur_product is not None:
            item['URL'] = cur_product['Product_URL']
            item['Product_Quantity'] = int(item['Product_Quantity'])
            item['Product_Name'] = cur_product['Product_Name']
            item['Product_Price'] = int(cur_product['Product_Price'])
            item['Shop_Name'] = cur_product['Shop_Name']
            total_price = total_price+item['Product_Quantity']*item['Product_Price']
    return render_template('cart_page.html',carts = carts,total_price=total_price)

@app.post('/move_to_orders')
def move_to_orders():
    carts = list(carts_tb.find(({'Id':session['id']})))
    for item in carts:
        cur_product = products_tb.find_one({'Product_Id':int(item['Product_Id'])},{'_id':0})
        if cur_product is not None:
            item['URL'] = cur_product['Product_URL']
            item['Product_Quantity'] = int(item['Product_Quantity'])
            item['Product_Name'] = cur_product['Product_Name']
            item['Product_Price'] = int(cur_product['Product_Price'])
            item['Shop_Name'] = cur_product['Shop_Name']
            orders_tb.insert_one({'Id':session['id'], 'Product_Id':item['Product_Id'], 'Product_Quantity':item['Product_Quantity'], 'Product_Name':item['Product_Name'], 'Product_Price':item['Product_Price'], 'Shop_Name':item['Shop_Name'], 'URL':item['URL']})
    carts = list(carts_tb.delete_many(({'Id':session['id']})))
    return jsonify({'msg':'SuccessDOne'})

@app.route('/view_orders',methods=['GET','POST'])
def view_orders():
    orders = orders_tb.find({'Shop_Name':session['shop_name']})
    return render_template('view_orders.html',orders = orders)

@app.get('/logout')
def logout():
    session['role']=None
    session['name']=None
    session['id']=None
    session['shop_name']=None
    return redirect(url_for('index'))

if __name__=="__main__":
    app.run(debug=True, host="192.168.3.150")