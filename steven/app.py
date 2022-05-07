from cProfile import label
from platform import node
from flask import Flask,render_template,jsonify,json,request,flash,redirect
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_marshmallow import Marshmallow
import requests
import urllib.request, json
from flask_httpauth import HTTPBasicAuth
from sqlalchemy import PickleType
from werkzeug.security import generate_password_hash,check_password_hash

from sqlalchemy.ext.mutable import MutableList

app = Flask(__name__)

app.config['SECRET_KEY'] = '5791628bb0b13ce0c676dfde280ba245'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
from flask_marshmallow import Marshmallow

db = SQLAlchemy(app)
migrate = Migrate(app, db)
ma= Marshmallow(app)

auth = HTTPBasicAuth()
users = {
    "john": generate_password_hash("hello"),
    "susan": generate_password_hash("bye")
}



class Ports(db.Model):
    port_id = db.Column(db.Integer, primary_key=True)
    port_name = db.Column(db.String(128))
    is_reserved = db.Column(db.Integer)
    reserved_by = db.Column(db.String(500))
    switch_id = db.Column(db.Integer)
    switch_is_reserved = db.Column(db.Integer)
    switch_reserved_by = db.Column(db.String(500))
    


class PortsSchema(ma.Schema):
    class Meta:
        fields = ("port_id","port_name","is_reserved","reserved_by","switch_id","switch_is_reserved","switch_reserved_by")


port_5_1 = Ports(port_name="Port 1",is_reserved=0,switch_id=4,switch_is_reserved=0)
port_5_2 = Ports(port_name="Port 2",is_reserved=0,switch_id=4,switch_is_reserved=0)

db.session.add(port_5_1)
db.session.add(port_5_2)
db.session.commit()

# p = Ports.query.filter_by(switch_id=4)

# for i in p:
#     db.session.delete(i)
# db.session.commit()


@auth.verify_password
def verify_password(username, password):
    if username in users and \
            check_password_hash(users.get(username), password):
        return username




@app.route('/get_all_ports')
def GetAllPorts():
    all_ports = Ports.query.all()
    ports_schema = PortsSchema(many=True)
    ports = ports_schema.dump(all_ports)
    
    return jsonify(ports)

def all_ports_reserved(ports):
    s = 0
    for port in ports:
        s += port.is_reserved
    if s + 1 == 5:
        return True
    return False



@app.route('/reserve_port')
def ReservePort():
    port_id = request.args.get('port_id')
    current_user = request.args.get('current_user')
    port = Ports.query.filter_by(port_id=port_id).first()

    ports = Ports.query.filter_by(switch_id = port.switch_id)
    
    if all_ports_reserved(ports) == True:
        for i in ports:
            i.switch_is_reserved = 1

    if port.is_reserved==0:
        port.is_reserved = 1
        port.reserved_by = current_user



        db.session.commit()

        return jsonify({
            "msg":"Reserved"
        })


    else:
        
        return jsonify({"msg":"Its Already Reserved By : "+str(port.reserved_by)})


@app.route('/unreserve_port')

def Unreserve():
    port_id = request.args.get('port_id')
    current_user = request.args.get('current_user')
    port = Ports.query.filter_by(port_id=port_id).first()

    if port.switch_is_reserved:
        ports = Ports.query.filter_by(switch_id = port.switch_id)
        for i in ports:
            i.switch_is_reserved = 0
    if port.is_reserved== 1 and port.reserved_by == current_user:
        port.is_reserved = 0
        port.reserved_by = None
        db.session.commit()

        return jsonify({
            "msg":"UnReserved"
        })
    else:
        return jsonify({
            "msg":"You have Not Reserved it"
        })



def userid(users,user):
    for i in users:
        if i['label']== user:
            return i['id']

@app.route('/graph')
@auth.login_required

def graph():
    response = urllib.request.urlopen("http://127.0.0.1:5000/get_all_ports")
    data = response.read()
    dict = json.loads(data)
    
    port_nodes = [{'id': i["port_id"], 'label': i['port_name']} for i in dict]
    switch_nodes = [{'id': i, 'label': ('Switch  ' + str(i-20))} for i in range(len(port_nodes)+1,len(port_nodes)+5)]

    
    nodes = port_nodes + switch_nodes
    main_port = {'id': len(nodes) + 1, 'label': 'Main switch'}
    nodes.append(main_port)
    user_nodes = [{'id': i + 1 + len(nodes), 'label': j} for i,j in enumerate(users.keys())]
    nodes = nodes + user_nodes
    

    edge_main_switch = [{'from' : main_port['id'], 'to': i['id']} for i in switch_nodes]


    edge_to_switches = list()
    c_i = 1
    for i in switch_nodes:
        for _ in range(5):
            edge_to_switches.append({'from' : i['id'], 'to': c_i})
            c_i += 1


    edge_to_port = [{'from' : i['port_id'], 'to': userid(user_nodes,i['reserved_by'])} for i in dict if i['is_reserved'] == 1]


    edges = edge_main_switch + edge_to_switches + edge_to_port


    return render_template('graph.html',nodes = nodes, edges = edges)


def same_member(switch):
    
    ports = Ports.query.filter_by(switch_id = switch)
    members = []
    for port in ports:
        members.append(port.reserved_by)
    return list(set(members))

@app.route('/',methods=["GET","POST"])
@auth.login_required
def switch():   
    
    response = urllib.request.urlopen("http://127.0.0.1:5000/get_all_ports")
    data = response.read()
    dict = json.loads(data)
    switches = [{"switch_name":"Switch 1","switch_id":0},
                {"switch_name":"Switch 2","switch_id":1},
                {"switch_name":"Switch 3","switch_id":2},
                {"switch_name":"Switch 4","switch_id":3},
                {"switch_name":"Switch 5","switch_id":4},]

    for i in switches:
        for j in dict:
            if i['switch_id'] == j['switch_id']:
                i["switch_is_reserved"] = j['switch_is_reserved']
                i['switch_reserved_by'] = j['reserved_by']
                i["members"] = same_member(i['switch_id'])
                break
    

    return render_template('index.html',switches = switches,username=auth.current_user())


@app.route('/ports/<int:switch_id>/<string:switch_name>',methods=["GET","POST"])
@auth.login_required
def ports(switch_id, switch_name):
    ports = Ports.query.filter_by(switch_id=switch_id)
    
   
   
    return render_template('ports.html',ports=ports,switch_name = switch_name,username=auth.current_user())
    


@app.route('/reserve_switch')

def ReserveSwitch():

    switch_id = request.args.get('switch_id')
    current_user = request.args.get('current_user')

    ports = Ports.query.filter_by(switch_id = switch_id)
    db.session.commit()
    for port in ports:
        
        port.is_reserved = 1
        port.reserved_by = current_user
        port.switch_is_reserved = 1
    db.session.commit()
    return jsonify({
        "msg":"Reserved"
    })


@app.route('/unreserve_switch')
def UnreserveSwitch():
    
    switch_id = request.args.get('switch_id')
    current_user = request.args.get('current_user')

    ports = Ports.query.filter_by(switch_id = switch_id)
    
    for port in ports:
        port.is_reserved = 0
        port.reserved_by = None
        port.switch_is_reserved = 0
    db.session.commit()
    return jsonify({
        "msg":"Reserved"
    })


@app.route('/reserve_or_unreserve_switch/<int:id>/<string:current_user>',methods=['GET', 'POST'])
@auth.login_required

def reserve_or_unreserve_switch(id,current_user):
    if request.method == "POST":
        if "reserve" in request.form:
            response = urllib.request.urlopen("http://127.0.0.1:5000/reserve_switch?switch_id="+str(id)+"&&current_user="+str(current_user))
            data = response.read()
            dict = json.loads(data)
            flash(str(dict['msg']))
            return redirect('/')
        else:
            response = urllib.request.urlopen("http://127.0.0.1:5000/unreserve_switch?switch_id="+str(id)+"&&current_user="+str(current_user))
            data = response.read()
            dict = json.loads(data)
            flash(str(dict['msg']))
            return redirect('/')



@app.route('/Reserve_or_unreserve/<int:id>/<string:current_user>',methods=['GET', 'POST'])
@auth.login_required

def reserve_or_unreserve(id,current_user):
    if request.method == "POST":
        if "reserve" in request.form:
            response = urllib.request.urlopen("http://127.0.0.1:5000/reserve_port?port_id="+str(id)+"&&current_user="+str(current_user))
            data = response.read()
            dict = json.loads(data)
            flash(str(dict['msg']))
            return redirect('/')
        else:
            response = urllib.request.urlopen("http://127.0.0.1:5000/unreserve_port?port_id="+str(id)+"&&current_user="+str(current_user))
            data = response.read()
            dict = json.loads(data)
            flash(str(dict['msg']))
            return redirect('/')




if __name__ == '__main__':
    app.run(debug=True)