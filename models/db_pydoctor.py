# -*- coding: utf-8 -*-
import html2text
from gluon.contrib.markdown.markdown2 import markdown

def advanced_repr(value, row):
    if not value:
        return ''
    mdtext=html2text.html2text(value)
    if len(mdtext)>=300:
        mdtext=mdtext[:280]+' ...'
    mdtext=mdtext.replace('\n',' ')
    return XML(markdown(mdtext))

db = DAL('sqlite://storage2.sqlite')
from gluon.tools import *

def advanced_editor(field, value):
    return TEXTAREA(_id = str(field).replace('.','_'),
                    _name=field.name,
                    _class='text ckeditor',
                    value=value, _cols=80, _rows=15)

auth = Auth(globals(),db)
auth.define_tables()
crud = Crud(globals(),db)

def persona_format(row):
    url=URL('default','admin_personas',args=['edit','persona',row.id],user_signature=True)
    img=IMG(_src=URL('static','personas.png'),_width=16,_height=16)
    img=CAT(img,B(' %(apellido)s,%(nombre)s '%row),row.cuitcuil)
    anchor=A(img,_href=url)
    return anchor

db.define_table('persona',
                Field('sexo',length=2, requires = IS_IN_SET({'F':'Femenino', 'M':'Masculino', 'J':'Persona Jurídica'},
                                                   zero=T('Elija persona jurídica o sexo'),
                                                   error_message='debe elegir persona jurídica o sexo persona física')),
                Field('apellido',length=70,required=True,label=T('Apellido o Razón Social')),
                Field('nombre',length=100,label=T('Nombre')),
                Field('cuitcuil',length=20,required=True,label=T('CUIT/CUIL')),
                Field('domicilio',length=150,required=True,label=T('Domicilio')),
                Field('email',length=150,requires=IS_EMPTY_OR(IS_EMAIL()),label=T('E-Mail')),
                Field('observaciones','text',length=65535,label=T('Observaciones'),
                      widget = advanced_editor,
                      represent = advanced_repr ),
                Field('telefono',length=50,label=T('Teléfono')),
                Field('celular',length=50,label=T('Celular')),
                Field('fotografia','upload',length=65536,requires = IS_EMPTY_OR(IS_IMAGE())),
                Field('matricula',length=10,label=T('Matrícula'),comment=T('Matrícula profesional de abogado')),
                Field('domiciliolegal',length=150,label=T('Domicilio Legal'),comment=T('Domicilio legal del abogado')),
                auth.signature,
               format=persona_format)
db.persona.id.readable=db.persona.id.writable=False

db.define_table('fuero',
                Field('descripcion',length=60,required=True,label=T('Descripción')),
               format='%(descripcion)s')
db.fuero.id.readable=db.fuero.id.writable=False

db.define_table('instancia',
                Field('descripcion',length=60,required=True,label=T('Descripción')),
               format='%(descripcion)s')
db.instancia.id.readable=db.instancia.id.writable=False

db.define_table('juzgado',
                Field('descripcion',length=120,required=True,label=T('Descripción')),
                Field('fuero_id',db.fuero,label=T('Fuero')),
                Field('instancia_id',db.instancia,label=T('Instancia')),
                auth.signature,
                format='%(descripcion)s')
#db.juzgado.fuero_id.widget = SQLFORM.widgets.autocomplete(
#     request, db.fuero.descripcion, id_field=db.fuero.id)
#db.juzgado.instancia_id.widget = SQLFORM.widgets.autocomplete(
#     request, db.instancia.descripcion, id_field=db.instancia.id)
db.juzgado.fuero_id.requires = IS_IN_DB(db,db.fuero.id,'%(descripcion)s')
db.juzgado.instancia_id.requires = IS_IN_DB(db,db.instancia.id,'%(descripcion)s')
db.juzgado.descripcion.requires = IS_NOT_IN_DB(db, 'juzgado.descripcion')
db.juzgado.id.readable=db.juzgado.id.writable=False

#Listado de tipos de proceso posibles.
db.define_table('tipoproceso',
               Field('descripcion',length=150,required=True,label=T('Descripción')),
               format='%(descripcion)s',
               singular=T('Tipo de proceso'),
               plural=T('Tipo de proceso'),)
db.fuero.id.readable=db.fuero.id.writable=False

def expediente_format(row):
    url=URL('default','admin_expedientes',args=['expediente','edit','expediente',row.id],user_signature=True)
    img=IMG(_src=URL('static','expedientes.png'),_width=16,_height=16)
    img=CAT(img,' %(numero)s %(caratula)s'%row)
    anchor=A(img,_href=url)
    return anchor


db.define_table('expediente',
                Field('numero',length=40,requires = IS_NOT_IN_DB(db, 'expediente.numero'),label=T('Nº')),
                Field('caratula',length=200,required=True, label=T('Carátula')),
                Field('tipoproceso_id',db.tipoproceso, label=T('Tipo'),
                      comment=T('Tipo de proceso')),
                Field('juzgado_id',db.juzgado, label=T('Origen'),
                      comment=T('Juzgado o Fiscalía de origen')),
                Field('inicio','date', label=T('Fecha inicio')),
                Field('final','date', label=T('Fecha fin')),
                auth.signature,
               format=expediente_format)
#widget = lambda field, value:
    #SQLFORM.widgets.string.widget(field, value, _class='my-string')
db.expediente.id.readable=db.expediente.id.writable=False
db.expediente.juzgado_id.widget = SQLFORM.widgets.autocomplete(
     request, db.juzgado.descripcion, id_field=db.juzgado.id)
db.expediente.tipoproceso_id.widget = SQLFORM.widgets.autocomplete(
     request, db.tipoproceso.descripcion, id_field=db.tipoproceso.id)

autocomplete_expte_widget=SQLFORM.widgets.autocomplete(
     request, db.expediente.numero, id_field=db.expediente.id)
def movimiento_titulo(value,row):
    if row.estado != 'B':
        value=B(value)
    if row.estado != 'P':
        value=I(value)
    return value

db.define_table('movimiento',
                Field('expediente_id',db.expediente, widget=autocomplete_expte_widget),
                Field('estado',length=2,readable=False,
                      requires = IS_IN_SET({'P':'Procesal', 'E':'Extraprocesal','B':'Borrador'},
                          zero=None,
                          error_message='Seleccione estado del movimiento')),
                Field('titulo',length=150,required=True, label=T('Título'), represent=movimiento_titulo),
                Field('texto','text',length=65536,label=T('Texto'),
                      requires = IS_NOT_EMPTY(),
                      widget = advanced_editor,
                      represent = advanced_repr ),
                Field('archivo','upload'),
                auth.signature,
                singular = T("Movimiento"), plural = T("Movimientos"),
               format='%(titulo)s')
db.movimiento.id.readable=db.movimiento.id.writable=False

colors=[(T('Urgente'),'#b94a48','glyphicon-fire'),
         (T('Prioritario'),'#c09853','glyphicon-exclamation-sign'),
         (T('Importante'),'#446e9b','glyphicon-star'),
         (T('Recordar'),'#468847','glyphicon-heart')]
prioridad_set=dict([(k,v[0]) for k,v in enumerate(colors)])
'''
446e9b	blue
c09853	yellow
b94a48	red
468847	green'''

def agenda_titulo(value,row):
    p=colors[int(row.prioridad)]
    icon=SPAN('',_style="color:%s"%p[1],_class="glyphicon %s"%p[2])
    if row.estado == 'R':
        icon+=SPAN('',_class="glyphicon glyphicon-ok")
    elif row.estado == 'C':
        icon+=SPAN('',_class="glyphicon glyphicon-remove")
    #value=
    if row.estado == 'C':
        value=I(value)
    elif row.estado == 'P':
        value=B(value)
    value=P(icon+' '+value)
    return value

db.define_table('agenda',
                Field('expediente_id',db.expediente, widget=autocomplete_expte_widget),
                Field('vencimiento','datetime',label=T('Vence en')),
                Field('cumplido','datetime',label=T('Cumplido el')),
                Field('prioridad',length=2,readable=False, 
                      requires = IS_IN_SET(prioridad_set,
                          zero=None,
                          error_message='Elija una prioridad')),
                Field('estado', length=2, readable=False, 
                      requires = IS_IN_SET({'P': T('Pendiente'), 'C':T('Cancelada'), 'R': T('Realizada')},
                          zero=None,
                          error_message=T('Establezca un estado'))),
                Field('titulo',length=150,required=True, label=T('Título'), represent = agenda_titulo),
                Field('texto','text',length=65536,label=T('Texto'),widget = advanced_editor, represent = advanced_repr),
                auth.signature)

db.agenda.id.readable=db.agenda.id.writable=False

db.define_table('parte',
                Field('expediente_id',db.expediente, widget=autocomplete_expte_widget),
                Field('persona_id',db.persona,label=T('Persona')),
                Field('caracter',length=80,label=T('Carácter'),comment=T('Carácter en que se presenta la parte: actor, demandado, imputado, etc')),
                Field('observaciones','text',length=65536,widget = advanced_editor, represent = advanced_repr ),
                auth.signature)

db.parte.id.readable=db.parte.id.writable=False
