#!/usr/bin/env python3
"""Generate editable diagrams with embedded, portable vector illustrations.
Re-export with the draw.io desktop CLI; labels and connectors stay native.
"""
from pathlib import Path
from xml.etree.ElementTree import Element, SubElement, ElementTree
import random
from urllib.parse import quote

HERE = Path(__file__).resolve().parent
BLUE = '#317db2'
TEAL = '#178c91'
PURPLE = '#8061ac'
INK = '#1d3e6f'
MUTED = '#61788c'


def svg_icon(kind):
    defs = '''<defs><linearGradient id="screen" x2="1" y2="1"><stop stop-color="#eff8ff"/><stop offset="1" stop-color="#bddceb"/></linearGradient><linearGradient id="metal" x2="1" y2="1"><stop stop-color="#b6ceda"/><stop offset="1" stop-color="#617c91"/></linearGradient><linearGradient id="blue" x2="1" y2="1"><stop stop-color="#4c9bcd"/><stop offset="1" stop-color="#1d4e77"/></linearGradient></defs>'''
    shadow='<ellipse cx="60" cy="96" rx="47" ry="5" fill="#eaf0f4"/>'
    network=''.join(f'<path d="M{x1} {y1}L{x2} {y2}" stroke="#7eaec9" stroke-width="2"/>' for x1,y1 in [(32,32),(32,68)] for x2,y2 in [(59,23),(59,50),(59,77)])+''.join(f'<path d="M{x1} {y1}L90 {y2}" stroke="#7eaec9" stroke-width="2"/>' for x1,y1 in [(59,23),(59,50),(59,77)] for y2 in [33,68])+''.join(f'<circle cx="{x}" cy="{y}" r="7" fill="{c}" stroke="white" stroke-width="2"/>' for x,y,c in [(32,32,BLUE),(32,68,BLUE),(59,23,TEAL),(59,50,TEAL),(59,77,TEAL),(90,33,PURPLE),(90,68,PURPLE)])
    if kind == 'network':
        art=network
    elif kind=='agent':
        art='''<path d="M59 9V22" stroke="#6b879b" stroke-width="4"/><circle cx="59" cy="8" r="6" fill="#75c7c7"/><rect x="22" y="24" width="76" height="55" rx="15" fill="url(#metal)" stroke="#54768e" stroke-width="2"/><rect x="31" y="34" width="58" height="31" rx="9" fill="#173d61"/><circle cx="46" cy="48" r="5" fill="#8ce1dc"/><circle cx="74" cy="48" r="5" fill="#8ce1dc"/><path d="M47 70H73" stroke="#dceaf3" stroke-width="3" stroke-linecap="round"/><rect x="16" y="41" width="7" height="22" rx="3" fill="#638399"/><rect x="98" y="41" width="7" height="22" rx="3" fill="#638399"/><path d="M40 80L31 94H89L80 80" fill="url(#blue)"/>'''
    elif kind=='environment':
        art='''<path d="M6 64L58 37L115 65L63 94Z" fill="#d9e9ed"/><path d="M34 52L59 40L92 56L68 69Z" fill="#c0d9e4"/><path d="M29 56L58 70L92 53" stroke="white" stroke-width="6" fill="none"/><path d="M63 29L87 17L105 28V60L82 73L63 60Z" fill="#367eac"/><path d="M63 29L81 40L105 28" fill="#72b2d6"/><path d="M81 40V73" stroke="#c4e0ee" stroke-width="2"/><path d="M69 37V45M76 41V49M87 44V52M96 39V47M87 56V64M96 51V59" stroke="#e3f2f7" stroke-width="4"/><path d="M24 58V78" stroke="#9e805e" stroke-width="5"/><circle cx="24" cy="47" r="15" fill="#61aaa2"/><circle cx="33" cy="53" r="10" fill="#39948f"/>'''
    elif kind=='memory':
        art='''<path d="M24 22H95V79C95 95 24 95 24 79Z" fill="url(#screen)" stroke="#6c98b2" stroke-width="2"/><ellipse cx="59.5" cy="22" rx="35.5" ry="13" fill="#d5e9f4" stroke="#6c98b2" stroke-width="2"/><path d="M24 47C24 63 95 63 95 47M24 70C24 86 95 86 95 70" fill="none" stroke="#83abc3" stroke-width="2"/><path d="M42 42L56 46L78 38" fill="none" stroke="#3688b4" stroke-width="3"/><circle cx="42" cy="42" r="4" fill="#178c91"/><circle cx="56" cy="46" r="4" fill="#178c91"/><circle cx="78" cy="38" r="4" fill="#178c91"/>'''
    elif kind=='server':
        art='''<path d="M28 18L48 7L100 24L80 36Z" fill="#5e879f"/><path d="M28 18L80 36V92L28 73Z" fill="#234b67"/><path d="M80 36L100 24V80L80 92Z" fill="#153751"/><path d="M35 28L73 41V54L35 41ZM35 45L73 58V71L35 58ZM35 62L73 75V85L35 72Z" fill="#3e6c87"/><path d="M42 34L65 42M42 51L65 59M42 68L65 76" stroke="#8fc0d3" stroke-width="2"/><circle cx="70" cy="48" r="2.4" fill="#71d7b8"/><circle cx="70" cy="65" r="2.4" fill="#71d7b8"/><circle cx="70" cy="81" r="2.4" fill="#71d7b8"/>'''
    elif kind=='laptop':
        art='''<rect x="20" y="14" width="80" height="62" rx="5" fill="#4b687e"/><rect x="25" y="19" width="70" height="50" rx="2" fill="url(#screen)"/><path d="M20 76H100L113 91H7Z" fill="#8daabd" stroke="#607c91" stroke-width="2"/><path d="M42 81H77L81 86H38Z" fill="#d1e1ec"/><path d="M40 40L58 28L78 43L60 58Z" fill="none" stroke="#518caf" stroke-width="2"/><path d="M40 40L60 58M58 28L78 43" stroke="#518caf" stroke-width="2"/><circle cx="40" cy="40" r="5" fill="#317db2"/><circle cx="58" cy="28" r="5" fill="#178c91"/><circle cx="78" cy="43" r="5" fill="#8061ac"/><circle cx="60" cy="58" r="5" fill="#317db2"/>'''
    elif kind=='phone':
        art='''<rect x="34" y="7" width="52" height="86" rx="9" fill="#607e94"/><rect x="39" y="14" width="42" height="67" rx="3" fill="url(#screen)"/><path d="M51 11H69" stroke="#d6e6ef" stroke-width="2"/><circle cx="60" cy="87" r="3" fill="#d6e6ef"/><path d="M49 41L66 29L71 58L49 41L54 65L71 58" fill="none" stroke="#78a5bd" stroke-width="2"/><circle cx="49" cy="41" r="5" fill="#317db2"/><circle cx="66" cy="29" r="5" fill="#178c91"/><circle cx="71" cy="58" r="5" fill="#8061ac"/><circle cx="54" cy="65" r="5" fill="#178c91"/>'''
    elif kind=='documents':
        art='''<rect x="35" y="9" width="64" height="78" rx="5" fill="#c9dfe9" stroke="#9eb7c7" stroke-width="2"/><rect x="21" y="16" width="64" height="78" rx="5" fill="#f0f7fb" stroke="#779db5" stroke-width="2"/><path d="M32 29H73M32 37H60M32 76H73M32 83H60" stroke="#a5c1d1" stroke-width="3"/><circle cx="40" cy="57" r="7" fill="#5a9bc0"/><path d="M55 65L63 47L74 65Z" fill="#65aaa2"/>'''
    elif kind=='knowledge':
        art='''<path d="M20 32L65 17L103 35L59 52Z" fill="#81b9ca"/><path d="M20 32V49L59 68V52Z" fill="#3d87a0"/><path d="M59 52L103 35V51L59 68Z" fill="#dcecf0"/><path d="M20 54L59 73L103 56V72L59 89L20 70Z" fill="#a5bed8" stroke="#7295b9" stroke-width="1.5"/><path d="M28 59L59 75L96 61M29 66L59 81L96 67" fill="none" stroke="white" stroke-width="2"/>'''
    elif kind=='chart':
        art='''<rect x="21" y="8" width="72" height="83" rx="5" fill="#edf5fa" stroke="#8daabd" stroke-width="2"/><path d="M33 71V49H44V71ZM50 71V35H61V71ZM67 71V22H78V71Z" fill="#6a9ec0"/><path d="M31 76H81" stroke="#88a5b8" stroke-width="2"/><circle cx="90" cy="74" r="20" fill="#f0faf7" stroke="#69b3a6" stroke-width="2"/><path d="M80 74L87 81L101 66" fill="none" stroke="#388d7d" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/>'''
    elif kind in ['noise','intermediate','sample']:
        art='''<rect x="14" y="9" width="92" height="83" rx="8" fill="#f6fafc" stroke="#8daabd" stroke-width="2"/>'''
        if kind!='noise':
            art+='''<path d="M20 85V65L43 39L66 66L80 50L100 78V85Z" fill="#69aca6"/><path d="M20 85V76L45 57L67 76L84 67L100 82V85Z" fill="#3a7c98"/><circle cx="80" cy="29" r="9" fill="#ecc479"/>'''
        if kind!='sample':
            rng=random.Random(11)
            for i in range(100):
                art+=f'<circle cx="{rng.randint(21,99)}" cy="{rng.randint(17,84)}" r="{rng.choice([1.8,2.2,2.7])}" fill="{rng.choice(["#6c8fa9","#9fb9cf","#c2d4e2","#4e7494"])}" opacity="{1 if kind=="noise" else .6}"/>'
    elif kind=='flow':
        art=''
        for x,y,a in [(24,22,-25),(54,20,-5),(86,22,20),(24,50,-15),(54,48,0),(86,50,15),(24,78,-20),(54,78,5),(86,78,20)]:
            art+=f'<g transform="rotate({a} {x} {y})"><path d="M{x-8} {y}H{x+11}M{x+5} {y-5}L{x+11} {y}L{x+5} {y+5}" fill="none" stroke="#5b9fb8" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/></g>'
    elif kind=='features':
        art='''<rect x="16" y="9" width="88" height="82" rx="6" fill="#f2f5fa" stroke="#94a9c2" stroke-width="2"/>'''
        colors=['#dce8f2','#a9cbdc','#659dbd','#8d72ae','#c8b6de']
        for row in range(4):
            for col in range(4):
                art+=f'<rect x="{26+col*18}" y="{19+row*16}" width="13" height="11" rx="2" fill="{colors[(row*3+col)%5]}"/>'
    elif kind=='explain':
        art='''<rect x="15" y="12" width="67" height="75" rx="5" fill="#f1f5fb" stroke="#94a9c2" stroke-width="2"/><path d="M26 27H69M26 37H65M26 67H62M26 77H57" stroke="#aac1d5" stroke-width="3"/><rect x="25" y="45" width="46" height="12" rx="3" fill="#c6b8e0"/><circle cx="79" cy="59" r="21" fill="#f2fafc" fill-opacity=".7" stroke="#7d66a7" stroke-width="5"/><path d="M94 75L111 92" stroke="#574576" stroke-width="9" stroke-linecap="round"/>'''
    else:
        raise ValueError(kind)
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="120" height="104" viewBox="0 0 120 104">{defs}{shadow}{art}</svg>'


class Diagram:
    def __init__(self,slug):
        self.slug=slug
        self.doc=Element('mxfile',host='app.diagrams.net',agent='Peizhong research diagrams',version='24.7.17')
        d=SubElement(self.doc,'diagram',name='System overview',id=slug)
        model=SubElement(d,'mxGraphModel',dx='1040',dy='500',grid='1',gridSize='10',guides='1',tooltips='1',connect='1',arrows='1',fold='1',page='0',pageScale='1',pageWidth='1040',pageHeight='500',math='0',shadow='0',background='#ffffff')
        self.root=SubElement(model,'root');SubElement(self.root,'mxCell',id='0');SubElement(self.root,'mxCell',id='1',parent='0')
        self.n=0
    def vertex(self,label,x,y,w,h,style):
        self.n+=1; id=f'n{self.n}'
        c=SubElement(self.root,'mxCell',id=id,value=label,style=style,vertex='1',parent='1')
        SubElement(c,'mxGeometry',x=str(x),y=str(y),width=str(w),height=str(h),**{'as':'geometry'})
        return id
    def text(self,label,x,y,w,h=27,size=21,color=INK,bold=False):
        return self.vertex(label,x,y,w,h,f'text;html=0;strokeColor=none;fillColor=none;align=center;verticalAlign=middle;whiteSpace=wrap;rounded=0;fontFamily=Arial;fontSize={size};fontColor={color};fontStyle={1 if bold else 0};')
    def icon(self,kind,x,y,title,subtitle='',w=120,h=104,halo=True):
        if halo:self.vertex('',x-6,y-6,w+12,h+12,'ellipse;fillColor=#f0f6fa;strokeColor=none;')
        data=quote(svg_icon(kind), safe='')
        id=self.vertex('',x,y,w,h,f'shape=image;verticalLabelPosition=bottom;verticalAlign=top;imageAspect=0;aspect=fixed;image=data:image/svg+xml,{data};')
        self.text(title,x-70,y+h+6,w+140,30,bold=True)
        if subtitle:self.text(subtitle,x-90,y+h+37,w+180,25,17,MUTED)
        return id
    def arrow(self,x1,y1,x2,y2,color=BLUE,points=(),dashed=False):
        self.n+=1
        e=SubElement(self.root,'mxCell',id=f'e{self.n}',value='',edge='1',parent='1',style=f'curved=1;html=0;rounded=1;endArrow=block;endFill=1;strokeColor={color};strokeWidth=3;{ "dashed=1;dashPattern=5 4;" if dashed else ""}')
        g=SubElement(e,'mxGeometry',relative='1',**{'as':'geometry'})
        SubElement(g,'mxPoint',x=str(x1),y=str(y1),**{'as':'sourcePoint'})
        SubElement(g,'mxPoint',x=str(x2),y=str(y2),**{'as':'targetPoint'})
        if points:
            a=SubElement(g,'Array',**{'as':'points'})
            for x,y in points:SubElement(a,'mxPoint',x=str(x),y=str(y))
    def note(self,label,x,y,w,color=BLUE):
        # Place labels beside connectors; an opaque label background must never mask a flow.
        return self.vertex(label,x,y,w,26,f'text;html=0;strokeColor=none;fillColor=none;align=center;verticalAlign=middle;whiteSpace=wrap;fontFamily=Arial;fontSize=18;fontColor={color};spacing=3;')
    def save(self):
        ElementTree(self.doc).write(HERE/f'{self.slug}.drawio',encoding='utf-8',xml_declaration=True)


def reinforcement():
    d=Diagram('reinforcement-learning')
    d.arrow(285,122,716,122,points=[(485,58)])
    d.arrow(710,175,280,175,TEAL,points=[(500,320)])
    d.arrow(745,270,564,346,PURPLE,points=[(675,342)],dashed=True)
    d.arrow(374,369,210,270,PURPLE,points=[(263,367)],dashed=True)
    d.icon('agent',144,96,'Agent / policy','Choose an action')
    d.icon('environment',729,96,'Environment','Dynamics & outcomes')
    d.icon('memory',436,332,'Learning update','Improve expected return',w=110,h=95)
    d.note('Action',421,42,145)
    d.note('Reward + next state',391,278,224,TEAL)
    d.note('Experience',635,355,140,PURPLE)
    d.note('Updated policy',239,395,160,PURPLE)
    d.save()


def federated():
    d=Diagram('federated-learning')
    d.arrow(232,129,438,194,TEAL,points=[(335,125)],dashed=True)
    d.arrow(436,235,232,183,BLUE,points=[(333,252)])
    d.arrow(763,125,577,191,TEAL,points=[(652,126)],dashed=True)
    d.arrow(575,235,765,178,BLUE,points=[(667,249)])
    d.arrow(450,407,444,252,TEAL,points=[(350,389),(350,304)],dashed=True)
    d.arrow(577,252,570,407,BLUE,points=[(674,304),(674,389)])
    d.icon('laptop',95,71,'Client A','Train on local data')
    d.icon('server',450,170,'Coordinator','Aggregate local updates')
    d.icon('phone',780,65,'Client B','Train on local data')
    d.icon('laptop',456,368,'Client C','Train on local data',w=108,h=94)
    d.note('Model updates',251,90,172,TEAL)
    d.note('Global model',230,255,152)
    d.note('Model updates',607,89,177,TEAL)
    d.note('Global model',645,252,155)
    d.note('Raw training data stay at each client',310,22,410,TEAL)
    d.save()


def continual():
    d=Diagram('continual-transfer-learning')
    d.arrow(192,116,347,116,points=[(267,88)])
    d.arrow(507,116,662,116,points=[(580,88)])
    d.arrow(822,120,581,310,TEAL,points=[(930,163),(815,295)])
    d.arrow(421,345,253,345,PURPLE,points=[(330,383)],dashed=True)
    d.arrow(175,287,365,151,PURPLE,points=[(213,211)],dashed=True)
    d.icon('documents',73,62,'Task 1','Initial training')
    d.icon('network',370,62,'Shared learner','Update across tasks')
    d.icon('documents',690,62,'Task 2 → Task 3','New tasks & domains')
    d.icon('laptop',444,290,'Adapted model','Transfer useful features')
    d.icon('knowledge',108,291,'Retained knowledge','Limit forgetting')
    d.note('Learn',229,54,92)
    d.note('Continue learning',508,54,178)
    d.note('Adapt',742,329,85,TEAL)
    d.note('Preserve',278,377,124,PURPLE)
    d.note('Reuse',270,243,90,PURPLE)
    d.save()


def diffusion():
    d=Diagram('diffusion-flow-matching')
    d.arrow(198,105,371,105,points=[(285,83)])
    d.arrow(522,105,701,105,points=[(615,83)])
    d.arrow(198,345,371,345,TEAL,points=[(285,324)])
    d.arrow(522,345,701,345,TEAL,points=[(615,324)])
    d.icon('noise',81,67,'Noise','Random initial sample',w=112,h=97)
    d.icon('intermediate',389,67,'Denoising steps','Learn reverse dynamics',w=112,h=97)
    d.icon('sample',720,67,'Generated data','Structured samples',w=112,h=97)
    d.icon('noise',81,309,'Noise','Base distribution',w=112,h=97)
    d.icon('flow',389,309,'Learned velocity','Integrate a continuous flow',w=112,h=97)
    d.icon('sample',720,309,'Generated data','Target distribution',w=112,h=97)
    d.note('Diffusion',42,14,188,PURPLE)
    d.note('Flow matching',42,257,188,TEAL)
    d.note('Iterative denoising',208,43,175)
    d.note('Refine',565,43,92)
    d.note('Follow velocity',214,284,163,TEAL)
    d.note('Transport',552,284,125,TEAL)
    d.save()


def interpretability():
    d=Diagram('interpretability-generalization')
    d.arrow(205,215,387,215,points=[(295,183)])
    d.arrow(530,184,729,112,PURPLE,points=[(617,114)])
    d.arrow(531,245,729,382,TEAL,points=[(651,278)])
    d.arrow(238,393,728,393,TEAL,points=[(476,445)],dashed=True)
    d.icon('documents',75,173,'Training data','Fit model parameters',w=112,h=97)
    d.icon('network',394,167,'Learned model','Representations & predictions')
    d.icon('explain',744,46,'Interpretable features','Explain model behavior',w=112,h=97)
    d.icon('chart',744,345,'Generalization','Evaluate on unseen examples',w=112,h=97)
    d.icon('documents',104,351,'Held-out data','Separate from training',w=94,h=81)
    d.note('Learn',260,169,91)
    d.note('Inspect',548,73,105,PURPLE)
    d.note('Predict',620,240,96,TEAL)
    d.note('Independent evaluation',355,448,240,TEAL)
    d.save()


if __name__=='__main__':
    for make in [reinforcement,federated,continual,diffusion,interpretability]:make()
    print('Generated 5 editable draw.io sources.')
