// ============================================================
// 央企穿透式资金监管 — GraphDB实体关系 + 7大领域 + 106指标
// ============================================================

// ── 7大监管领域定义 + 106个指标
var DOMAINS = [
  {id:'fund', name:'资金管理', color:'#00d8ff', icon:'F',
   indicators:[
     {id:'f01',name:'资金归集率',unit:'%',threshold:[85,95],direction:'up'},
     {id:'f02',name:'日均现金余额',unit:'亿',threshold:[null,null],direction:'up'},
     {id:'f03',name:'流动性覆盖率(LCR)',unit:'%',threshold:[100,150],direction:'up'},
     {id:'f04',name:'净稳定资金比率(NSFR)',unit:'%',threshold:[100,120],direction:'up'},
     {id:'f05',name:'资金池利用率',unit:'%',threshold:[50,90],direction:'mid'},
     {id:'f06',name:'银行账户数量',unit:'个',threshold:[null,null],direction:'down'},
     {id:'f07',name:'大额支付审批率',unit:'%',threshold:[95,100],direction:'up'},
     {id:'f08',name:'资金预算执行率',unit:'%',threshold:[85,100],direction:'up'},
     {id:'f09',name:'内部资金调拨效率',unit:'天',threshold:[null,3],direction:'down'},
     {id:'f10',name:'闲置资金比例',unit:'%',threshold:[null,15],direction:'down'},
     {id:'f11',name:'现金流预测偏差',unit:'%',threshold:[null,10],direction:'down'},
     {id:'f12',name:'银企直连覆盖率',unit:'%',threshold:[80,95],direction:'up'},
     {id:'f13',name:'资金集中度',unit:'%',threshold:[70,90],direction:'up'},
     {id:'f14',name:'支付异常交易数',unit:'笔',threshold:[null,5],direction:'down'},
     {id:'f15',name:'资金周转天数',unit:'天',threshold:[null,45],direction:'down'},
   ]},
  {id:'debt', name:'债务管理', color:'#ffaa00', icon:'D',
   indicators:[
     {id:'d01',name:'资产负债率',unit:'%',threshold:[null,65],direction:'down'},
     {id:'d02',name:'有息负债规模',unit:'亿',threshold:[null,null],direction:'down'},
     {id:'d03',name:'带息负债比率',unit:'%',threshold:[null,50],direction:'down'},
     {id:'d04',name:'综合融资成本',unit:'%',threshold:[null,5.5],direction:'down'},
     {id:'d05',name:'短期债务占比',unit:'%',threshold:[null,40],direction:'down'},
     {id:'d06',name:'债务到期集中度',unit:'%',threshold:[null,30],direction:'down'},
     {id:'d07',name:'利息保障倍数',unit:'倍',threshold:[2,5],direction:'up'},
     {id:'d08',name:'EBITDA/有息负债',unit:'%',threshold:[15,30],direction:'up'},
     {id:'d09',name:'再融资缺口',unit:'亿',threshold:[null,50],direction:'down'},
     {id:'d10',name:'信用评级',unit:'级',threshold:[null,null],direction:'up'},
     {id:'d11',name:'债券发行利差',unit:'bp',threshold:[null,150],direction:'down'},
     {id:'d12',name:'银行授信使用率',unit:'%',threshold:[50,85],direction:'mid'},
     {id:'d13',name:'非标融资占比',unit:'%',threshold:[null,20],direction:'down'},
     {id:'d14',name:'永续债规模',unit:'亿',threshold:[null,null],direction:'down'},
     {id:'d15',name:'或有负债比率',unit:'%',threshold:[null,10],direction:'down'},
   ]},
  {id:'guarantee', name:'担保管理', color:'#ff2020', icon:'G',
   indicators:[
     {id:'g01',name:'对外担保余额',unit:'亿',threshold:[null,null],direction:'down'},
     {id:'g02',name:'担保/净资产比',unit:'%',threshold:[null,40],direction:'down'},
     {id:'g03',name:'关联担保占比',unit:'%',threshold:[null,30],direction:'down'},
     {id:'g04',name:'超限额担保笔数',unit:'笔',threshold:[null,0],direction:'down'},
     {id:'g05',name:'担保集中度(前5)',unit:'%',threshold:[null,60],direction:'down'},
     {id:'g06',name:'反担保覆盖率',unit:'%',threshold:[80,120],direction:'up'},
     {id:'g07',name:'担保代偿率',unit:'%',threshold:[null,2],direction:'down'},
     {id:'g08',name:'未经审批担保',unit:'笔',threshold:[null,0],direction:'down'},
     {id:'g09',name:'对民企担保占比',unit:'%',threshold:[null,20],direction:'down'},
     {id:'g10',name:'担保链长度',unit:'层',threshold:[null,2],direction:'down'},
     {id:'g11',name:'或有担保损失准备',unit:'亿',threshold:[null,null],direction:'up'},
     {id:'g12',name:'担保审批时效',unit:'天',threshold:[null,5],direction:'down'},
     {id:'g13',name:'到期担保释放率',unit:'%',threshold:[80,95],direction:'up'},
     {id:'g14',name:'跨境担保占比',unit:'%',threshold:[null,15],direction:'down'},
     {id:'g15',name:'担保合规评分',unit:'分',threshold:[70,90],direction:'up'},
   ]},
  {id:'invest', name:'投资管理', color:'#a855f7', icon:'I',
   indicators:[
     {id:'i01',name:'投资总规模',unit:'亿',threshold:[null,null],direction:'mid'},
     {id:'i02',name:'投资回报率(ROI)',unit:'%',threshold:[5,12],direction:'up'},
     {id:'i03',name:'非主业投资占比',unit:'%',threshold:[null,15],direction:'down'},
     {id:'i04',name:'长期股权投资',unit:'亿',threshold:[null,null],direction:'mid'},
     {id:'i05',name:'投资项目数量',unit:'个',threshold:[null,null],direction:'mid'},
     {id:'i06',name:'亏损项目占比',unit:'%',threshold:[null,10],direction:'down'},
     {id:'i07',name:'投资决策合规率',unit:'%',threshold:[95,100],direction:'up'},
     {id:'i08',name:'PPP项目敞口',unit:'亿',threshold:[null,null],direction:'down'},
     {id:'i09',name:'境外投资占比',unit:'%',threshold:[null,25],direction:'down'},
     {id:'i10',name:'投后管理评分',unit:'分',threshold:[70,90],direction:'up'},
     {id:'i11',name:'退出项目回收率',unit:'%',threshold:[80,100],direction:'up'},
     {id:'i12',name:'在建工程超预算率',unit:'%',threshold:[null,10],direction:'down'},
     {id:'i13',name:'投资集中度',unit:'%',threshold:[null,40],direction:'down'},
     {id:'i14',name:'关联方投资占比',unit:'%',threshold:[null,20],direction:'down'},
     {id:'i15',name:'投资审批时效',unit:'天',threshold:[null,15],direction:'down'},
     {id:'i16',name:'股权投资减值率',unit:'%',threshold:[null,5],direction:'down'},
   ]},
  {id:'derivative', name:'金融衍生品', color:'#00ffb3', icon:'V',
   indicators:[
     {id:'v01',name:'衍生品名义本金',unit:'亿',threshold:[null,null],direction:'mid'},
     {id:'v02',name:'套保比率',unit:'%',threshold:[60,90],direction:'up'},
     {id:'v03',name:'MTM损益',unit:'万',threshold:[null,null],direction:'up'},
     {id:'v04',name:'VaR(95%)',unit:'万',threshold:[null,5000],direction:'down'},
     {id:'v05',name:'保证金占用',unit:'亿',threshold:[null,null],direction:'down'},
     {id:'v06',name:'交易对手集中度',unit:'%',threshold:[null,50],direction:'down'},
     {id:'v07',name:'套保有效性',unit:'%',threshold:[80,125],direction:'mid'},
     {id:'v08',name:'投机性交易占比',unit:'%',threshold:[null,5],direction:'down'},
     {id:'v09',name:'止损触发次数',unit:'次',threshold:[null,3],direction:'down'},
     {id:'v10',name:'衍生品到期集中度',unit:'%',threshold:[null,30],direction:'down'},
     {id:'v11',name:'CSA保证金充足率',unit:'%',threshold:[100,150],direction:'up'},
     {id:'v12',name:'ISDA协议覆盖率',unit:'%',threshold:[90,100],direction:'up'},
     {id:'v13',name:'衍生品合规评分',unit:'分',threshold:[70,90],direction:'up'},
     {id:'v14',name:'DV01敏感度',unit:'万/bp',threshold:[null,null],direction:'mid'},
     {id:'v15',name:'Greeks监控达标率',unit:'%',threshold:[85,100],direction:'up'},
   ]},
  {id:'finbiz', name:'金融业务', color:'#ffd060', icon:'B',
   indicators:[
     {id:'b01',name:'财务公司资本充足率',unit:'%',threshold:[10,15],direction:'up'},
     {id:'b02',name:'财务公司不良率',unit:'%',threshold:[null,2],direction:'down'},
     {id:'b03',name:'财务公司存贷比',unit:'%',threshold:[null,75],direction:'down'},
     {id:'b04',name:'融资租赁杠杆率',unit:'%',threshold:[null,70],direction:'down'},
     {id:'b05',name:'租赁资产逾期率',unit:'%',threshold:[null,3],direction:'down'},
     {id:'b06',name:'保险业务综合成本率',unit:'%',threshold:[null,100],direction:'down'},
     {id:'b07',name:'金融牌照合规状态',unit:'',threshold:[null,null],direction:'up'},
     {id:'b08',name:'关联交易占比',unit:'%',threshold:[null,30],direction:'down'},
     {id:'b09',name:'金融业务利润贡献',unit:'%',threshold:[null,null],direction:'up'},
     {id:'b10',name:'监管评级',unit:'级',threshold:[null,null],direction:'up'},
     {id:'b11',name:'流动性风险指标',unit:'%',threshold:[null,null],direction:'mid'},
     {id:'b12',name:'拨备覆盖率',unit:'%',threshold:[150,300],direction:'up'},
     {id:'b13',name:'行业集中度',unit:'%',threshold:[null,35],direction:'down'},
     {id:'b14',name:'单一客户集中度',unit:'%',threshold:[null,15],direction:'down'},
     {id:'b15',name:'金融合规评分',unit:'分',threshold:[70,90],direction:'up'},
   ]},
  {id:'overseas', name:'境外资金', color:'#ff6a2a', icon:'O',
   indicators:[
     {id:'o01',name:'境外资产规模',unit:'亿',threshold:[null,null],direction:'mid'},
     {id:'o02',name:'外汇敞口总额',unit:'亿',threshold:[null,null],direction:'down'},
     {id:'o03',name:'汇回率',unit:'%',threshold:[60,90],direction:'up'},
     {id:'o04',name:'外汇对冲比率',unit:'%',threshold:[50,80],direction:'up'},
     {id:'o05',name:'汇兑损益',unit:'万',threshold:[null,null],direction:'up'},
     {id:'o06',name:'境外负债率',unit:'%',threshold:[null,65],direction:'down'},
     {id:'o07',name:'跨境资金池效率',unit:'%',threshold:[70,90],direction:'up'},
     {id:'o08',name:'外管局合规状态',unit:'',threshold:[null,null],direction:'up'},
     {id:'o09',name:'境外税务合规',unit:'分',threshold:[70,90],direction:'up'},
     {id:'o10',name:'转移定价合规',unit:'分',threshold:[70,90],direction:'up'},
     {id:'o11',name:'国别风险评分',unit:'分',threshold:[60,85],direction:'up'},
     {id:'o12',name:'境外担保余额',unit:'亿',threshold:[null,null],direction:'down'},
     {id:'o13',name:'外币现金占比',unit:'%',threshold:[null,null],direction:'mid'},
     {id:'o14',name:'境外审计合规',unit:'分',threshold:[70,90],direction:'up'},
     {id:'o15',name:'境外合规评分',unit:'分',threshold:[70,90],direction:'up'},
   ]},
];

// ── 为每个实体生成指标数据（模拟）
function generateIndicators(node){
  if(node._indicators) return node._indicators;
  var seed = node.id.length*17+Math.round(node.compliance*3);
  function rng(){seed=(seed*9301+49297)%233280;return seed/233280;}
  var isHi=node.risk==='hi', isMd=node.risk==='md';
  var result={};
  DOMAINS.forEach(function(dom){
    var domData={score:0, indicators:[], alertCount:0};
    dom.indicators.forEach(function(ind){
      var val, status='normal';
      // Generate realistic values based on risk
      var base=rng();
      if(ind.unit==='%'){
        if(ind.direction==='up') val=isHi?(40+base*40):(isMd?(60+base*30):(75+base*20));
        else if(ind.direction==='down') val=isHi?(base*60+20):(isMd?(base*30+5):(base*15));
        else val=40+base*50;
      } else if(ind.unit==='亿'){
        val=isHi?(base*80+5):(isMd?(base*50+2):(base*30+1));
        val=Math.round(val*10)/10;
      } else if(ind.unit==='天'){
        val=isHi?(Math.round(base*10+3)):(isMd?(Math.round(base*5+1)):(Math.round(base*3)));
      } else if(ind.unit==='倍'){
        val=isHi?(0.5+base*2):(isMd?(1.5+base*3):(2.5+base*5));
        val=Math.round(val*10)/10;
      } else if(ind.unit==='分'){
        val=isHi?(45+base*30):(isMd?(65+base*25):(80+base*18));
        val=Math.round(val*10)/10;
      } else if(ind.unit==='笔'||ind.unit==='个'||ind.unit==='次'||ind.unit==='层'){
        val=isHi?(Math.round(base*8+1)):(isMd?(Math.round(base*3)):(Math.round(base*1)));
      } else if(ind.unit==='万'){
        val=isHi?((base-0.6)*8000):(isMd?((base-0.3)*3000):((base-0.1)*1000));
        val=Math.round(val);
      } else if(ind.unit==='bp'){
        val=isHi?(80+base*120):(isMd?(40+base*80):(10+base*50));
        val=Math.round(val);
      } else if(ind.unit==='级'){
        val=isHi?'BBB':(isMd?'A-':'AA-');
      } else {
        val=isHi?'\u5f85\u6574\u6539':(isMd?'\u5173\u6ce8':'\u5408\u89c4');
      }
      // Determine status: 红=低于阈值, 黄=阈值±10%, 绿=高于阈值10%+
      // direction: 'up'=越高越好(用threshold[0]作为阈值), 'down'=越低越好(用threshold[1]作为阈值), 'mid'=区间
      if(typeof val==='number'){
        var th=null;
        if(ind.direction==='up' && ind.threshold[0]!==null) th=ind.threshold[0];
        else if(ind.direction==='down' && ind.threshold[1]!==null) th=ind.threshold[1];
        else if(ind.direction==='mid' && ind.threshold[0]!==null) th=ind.threshold[0]; // use lower bound

        if(th!==null && th!==0){
          if(ind.direction==='up'){
            // up: 高于阈值好. 红:<阈值, 黄:阈值~阈值*1.1, 绿:>阈值*1.1
            if(val < th) status='danger';
            else if(val < th*1.1) status='warn';
            else status='normal';
          } else if(ind.direction==='down'){
            // down: 低于阈值好. 红:>阈值, 黄:阈值*0.9~阈值, 绿:<阈值*0.9
            if(val > th) status='danger';
            else if(val > th*0.9) status='warn';
            else status='normal';
          } else {
            // mid: 在区间内好
            var lo=ind.threshold[0]||0, hi=ind.threshold[1]||100;
            if(val<lo||val>hi) status='danger';
            else if(val<lo*1.1||val>hi*0.9) status='warn';
            else status='normal';
          }
        } else if(ind.threshold[1]!==null && ind.threshold[1]===0){
          // threshold is 0 (e.g. 超限额担保笔数 should be 0)
          if(val>0) status='danger';
          else status='normal';
        }
      }
      if(typeof val==='string'){
        status=val==='\u5f85\u6574\u6539'?'danger':(val==='\u5173\u6ce8'?'warn':'normal');
      }
      // Extra risk injection for high-risk entities
      if(isHi&&rng()>0.6&&status==='normal') status='danger';
      else if(isHi&&rng()>0.4&&status==='normal') status='warn';
      if(isMd&&rng()>0.75&&status==='normal') status='danger';
      else if(isMd&&rng()>0.5&&status==='normal') status='warn';

      if(status==='danger') domData.alertCount++;
      domData.indicators.push({
        id:ind.id, name:ind.name, unit:ind.unit,
        value:typeof val==='number'?Math.round(val*100)/100:val,
        status:status, threshold:ind.threshold, direction:ind.direction
      });
    });
    // Domain score
    var total=domData.indicators.length;
    var ok=domData.indicators.filter(function(x){return x.status==='normal';}).length;
    var warn=domData.indicators.filter(function(x){return x.status==='warn';}).length;
    domData.score=Math.round((ok*100+warn*60)/total);
    result[dom.id]=domData;
  });
  node._indicators=result;
  return result;
}

// ── 组织架构（同前，精简）
var ORG={id:'group',name:'中央企业集团',level:0,type:'集团',city:'北京',cash:4868000,debt:3421000,asset:18624000,guarantee:1286000,compliance:92.4,risk:'lo',
children:[
  {id:'east_group',name:'华东子集团',level:1,type:'二级子集团',city:'上海',cash:824000,debt:682000,asset:2840000,guarantee:456000,compliance:68.2,risk:'hi',
   children:[
     {id:'sh_industry',name:'上海实业',level:2,type:'三级子公司',city:'上海',cash:182000,debt:148000,asset:620000,guarantee:186000,compliance:72.4,risk:'hi',
      children:[
        {id:'pd_project',name:'浦东项目',level:3,type:'四级公司',city:'上海',cash:42000,debt:38000,asset:128000,guarantee:62000,compliance:65.8,risk:'hi',
         children:[{id:'pd_spv1',name:'浦东SPV-1',level:4,type:'五级SPV',city:'上海',cash:8200,debt:12000,asset:32000,guarantee:18000,compliance:58.2,risk:'hi',children:[]},
                   {id:'pd_spv2',name:'浦东SPV-2',level:4,type:'五级SPV',city:'上海',cash:12400,debt:8600,asset:28000,guarantee:0,compliance:82.4,risk:'lo',children:[]}]},
        {id:'sh_trade',name:'上海贸易',level:3,type:'四级公司',city:'上海',cash:28000,debt:22000,asset:86000,guarantee:24000,compliance:78.6,risk:'md',children:[]},
        {id:'sh_tech',name:'上海科技',level:3,type:'四级公司',city:'上海',cash:18000,debt:6000,asset:42000,guarantee:0,compliance:94.2,risk:'lo',children:[]}]},
     {id:'js_mfg',name:'江苏制造',level:2,type:'三级子公司',city:'南京',cash:124000,debt:96000,asset:480000,guarantee:82000,compliance:76.8,risk:'md',
      children:[{id:'nj_heavy',name:'南京重工',level:3,type:'四级公司',city:'南京',cash:48000,debt:42000,asset:186000,guarantee:36000,compliance:74.2,risk:'md',children:[]},
                {id:'sz_elec',name:'苏州电子',level:3,type:'四级公司',city:'苏州',cash:32000,debt:18000,asset:96000,guarantee:12000,compliance:88.4,risk:'lo',children:[]}]},
     {id:'zj_energy',name:'浙江能源',level:2,type:'三级子公司',city:'杭州',cash:186000,debt:142000,asset:640000,guarantee:64000,compliance:82.6,risk:'md',children:[]},
     {id:'ah_material',name:'安徽材料',level:2,type:'三级子公司',city:'合肥',cash:68000,debt:52000,asset:224000,guarantee:42000,compliance:78.4,risk:'md',children:[]}]},
  {id:'south_group',name:'华南子集团',level:1,type:'二级子集团',city:'深圳',cash:682000,debt:486000,asset:2420000,guarantee:182000,compliance:91.8,risk:'lo',
   children:[
     {id:'gz_trade',name:'广州贸易',level:2,type:'三级子公司',city:'广州',cash:186000,debt:124000,asset:620000,guarantee:48000,compliance:92.4,risk:'lo',children:[]},
     {id:'sz_tech',name:'深圳科技',level:2,type:'三级子公司',city:'深圳',cash:248000,debt:142000,asset:860000,guarantee:62000,compliance:94.2,risk:'lo',children:[]},
     {id:'fj_port',name:'福建港口',level:2,type:'三级子公司',city:'厦门',cash:124000,debt:96000,asset:420000,guarantee:36000,compliance:88.6,risk:'lo',children:[]}]},
  {id:'north_group',name:'华北子集团',level:1,type:'二级子集团',city:'天津',cash:568000,debt:424000,asset:1960000,guarantee:186000,compliance:78.4,risk:'md',
   children:[
     {id:'tj_heavy',name:'天津重工',level:2,type:'三级子公司',city:'天津',cash:142000,debt:124000,asset:520000,guarantee:68000,compliance:76.2,risk:'md',children:[]},
     {id:'hb_mining',name:'河北矿业',level:2,type:'三级子公司',city:'石家庄',cash:186000,debt:148000,asset:640000,guarantee:82000,compliance:74.8,risk:'md',children:[]},
     {id:'sd_chem',name:'山东化工',level:2,type:'三级子公司',city:'济南',cash:124000,debt:86000,asset:420000,guarantee:24000,compliance:86.2,risk:'lo',children:[]}]},
  {id:'sw_group',name:'西南子集团',level:1,type:'二级子集团',city:'成都',cash:426000,debt:384000,asset:1480000,guarantee:124000,compliance:62.8,risk:'hi',
   children:[
     {id:'cd_infra',name:'成都基建',level:2,type:'三级子公司',city:'成都',cash:86000,debt:124000,asset:420000,guarantee:62000,compliance:58.4,risk:'hi',
      children:[{id:'cd_road',name:'成都公路',level:3,type:'四级公司',city:'成都',cash:24000,debt:48000,asset:148000,guarantee:32000,compliance:54.2,risk:'hi',children:[]}]},
     {id:'cq_material',name:'重庆材料',level:2,type:'三级子公司',city:'重庆',cash:124000,debt:96000,asset:380000,guarantee:28000,compliance:72.6,risk:'md',children:[]},
     {id:'yn_resource',name:'云南资源',level:2,type:'三级子公司',city:'昆明',cash:96000,debt:82000,asset:320000,guarantee:18000,compliance:68.4,risk:'md',children:[]}]},
  {id:'nw_group',name:'西北子集团',level:1,type:'二级子集团',city:'西安',cash:384000,debt:286000,asset:1320000,guarantee:96000,compliance:88.6,risk:'lo',
   children:[
     {id:'xa_aero',name:'西安航空',level:2,type:'三级子公司',city:'西安',cash:148000,debt:96000,asset:520000,guarantee:42000,compliance:92.4,risk:'lo',children:[]},
     {id:'gs_petro',name:'甘肃石化',level:2,type:'三级子公司',city:'兰州',cash:96000,debt:82000,asset:320000,guarantee:28000,compliance:84.2,risk:'lo',children:[]}]},
  {id:'fin_group',name:'金融板块',level:1,type:'二级子集团',city:'北京',cash:1246000,debt:628000,asset:3240000,guarantee:86000,compliance:94.2,risk:'lo',
   children:[
     {id:'fin_co',name:'财务公司',level:2,type:'财务公司',city:'北京',cash:864000,debt:248000,asset:1860000,guarantee:24000,compliance:96.8,risk:'lo',children:[]},
     {id:'lease_co',name:'融资租赁',level:2,type:'租赁公司',city:'上海',cash:186000,debt:248000,asset:862000,guarantee:42000,compliance:82.6,risk:'md',children:[]}]},
  {id:'overseas_group',name:'境外板块',level:1,type:'二级子集团',city:'香港',cash:420000,debt:310000,asset:1240000,guarantee:86000,compliance:78.4,risk:'md',
   children:[
     {id:'hk_co',name:'香港控股',level:2,type:'境外子公司',city:'香港',cash:210000,debt:148000,asset:620000,guarantee:42000,compliance:86.4,risk:'md',children:[]},
     {id:'sg_co',name:'新加坡公司',level:2,type:'境外子公司',city:'新加坡',cash:80000,debt:62000,asset:248000,guarantee:24000,compliance:72.4,risk:'hi',children:[]},
     {id:'uk_co',name:'英国子公司',level:2,type:'境外子公司',city:'伦敦',cash:64000,debt:48000,asset:186000,guarantee:12000,compliance:82.6,risk:'lo',children:[]}]},
]};

// ── 关系类型
var REL_TYPES={
  'hasSubsidiary':{label:'控股',color:'rgba(0,216,255,0.35)',dash:[]},
  'fundFlow':{label:'资金归集',color:'rgba(0,255,179,0.35)',dash:[]},
  'guarantee':{label:'担保',color:'rgba(255,32,32,0.35)',dash:[6,3]},
  'borrowing':{label:'借贷',color:'rgba(255,170,0,0.35)',dash:[4,4]},
  'fxExposure':{label:'外汇敞口',color:'rgba(168,85,247,0.35)',dash:[3,3]},
};

// ── 全局状态
var drillPath=[ORG], currentNode=ORG, selectedNodeId=null;
var graphNodes=[], graphEdges=[];
var hoveredNodeId=null, dragNode=null, dragOffX=0, dragOffY=0;
var canvasW=0, canvasH=0;
var expandedDomains={}; // 右侧面板展开状态

// ── 工具
function fmtMoney(v){if(v>=10000)return(v/10000).toFixed(1)+'\u4ebf';return v.toFixed(0)+'\u4e07';}
function riskColor(r){return r==='hi'?'#ff2020':r==='md'?'#ffaa00':'#00d8ff';}
function riskGlow(r){return r==='hi'?'rgba(255,32,32,':r==='md'?'rgba(255,170,0,':'rgba(0,216,255,';}
function riskLabel(r){return r==='hi'?'\u9ad8\u98ce\u9669':r==='md'?'\u4e2d\u98ce\u9669':'\u4f4e\u98ce\u9669';}
function flatAll(n){var a=[n];if(n.children)n.children.forEach(function(c){a=a.concat(flatAll(c));});return a;}
function sumField(n,f){if(!n.children||!n.children.length)return n[f]||0;var s=0;n.children.forEach(function(c){s+=sumField(c,f);});return s;}
function findNode(id){var r=null;function s(n){if(n.id===id){r=n;return;}if(n.children)n.children.forEach(s);}s(ORG);return r;}

// ── 构建图数据
function buildGraphData(){
  graphNodes=[];graphEdges=[];
  var n=currentNode;
  var nodeR=n.children&&n.children.length?Math.min(32,Math.max(22,500/n.children.length)):28;
  graphNodes.push({id:n.id,data:n,x:canvasW/2,y:canvasH/2,r:42,fixed:true,isCenter:true,vx:0,vy:0});
  if(!n.children||!n.children.length)return;
  var count=n.children.length;
  var radius=Math.min(canvasW,canvasH)*0.33;
  n.children.forEach(function(c,i){
    var angle=(i/count)*Math.PI*2-Math.PI/2;
    var hasKids=c.children&&c.children.length;
    graphNodes.push({id:c.id,data:c,x:canvasW/2+Math.cos(angle)*radius+(Math.random()-0.5)*30,y:canvasH/2+Math.sin(angle)*radius+(Math.random()-0.5)*30,r:hasKids?nodeR+4:nodeR,fixed:false,isCenter:false,vx:0,vy:0});
    graphEdges.push({source:n.id,target:c.id,type:'hasSubsidiary'});
    if(c.cash>50000) graphEdges.push({source:c.id,target:n.id,type:'fundFlow'});
    if(c.guarantee>100000) graphEdges.push({source:n.id,target:c.id,type:'guarantee'});
  });
  // Cross relationships
  var kids=n.children;
  for(var i=0;i<kids.length;i++){
    if(kids[i].type.indexOf('\u5883\u5916')>=0||kids[i].id.indexOf('overseas')>=0||kids[i].id.indexOf('hk')>=0||kids[i].id.indexOf('sg')>=0){
      graphEdges.push({source:kids[i].id,target:n.id,type:'fxExposure'});
    }
  }
}

// ── 力导向
function simStep(){
  var repulsion=9000,attraction=0.004,centerPull=0.008;
  var cx=canvasW/2,cy=canvasH/2;
  for(var i=0;i<graphNodes.length;i++){
    var a=graphNodes[i];if(a.fixed)continue;
    var fx=0,fy=0;
    for(var j=0;j<graphNodes.length;j++){
      if(i===j)continue;var b=graphNodes[j];
      var dx=a.x-b.x,dy=a.y-b.y,dist=Math.sqrt(dx*dx+dy*dy)||1;
      fx+=(dx/dist)*repulsion/(dist*dist);fy+=(dy/dist)*repulsion/(dist*dist);
    }
    graphEdges.forEach(function(e){
      var other=null;
      if(e.source===a.id)other=graphNodes.find(function(n){return n.id===e.target;});
      else if(e.target===a.id)other=graphNodes.find(function(n){return n.id===e.source;});
      if(!other)return;
      var dx=other.x-a.x,dy=other.y-a.y,dist=Math.sqrt(dx*dx+dy*dy)||1;
      fx+=(dx/dist)*(dist-180)*attraction*10;fy+=(dy/dist)*(dist-180)*attraction*10;
    });
    fx+=(cx-a.x)*centerPull;fy+=(cy-a.y)*centerPull;
    a.vx=a.vx*0.55+fx*0.3;a.vy=a.vy*0.55+fy*0.3;
    a.x+=a.vx;a.y+=a.vy;
    a.x=Math.max(a.r+10,Math.min(canvasW-a.r-10,a.x));
    a.y=Math.max(a.r+10,Math.min(canvasH-a.r-10,a.y));
  }
}

// ── 绘制七瓣花节点
function drawDomainPetals(ctx,gn){
  var d=gn.data;
  var ind=generateIndicators(d);
  var cx=gn.x,cy=gn.y,r=gn.r;
  var isHover=(hoveredNodeId===gn.id),isSel=(selectedNodeId===gn.id);

  // 7 petals around the node
  DOMAINS.forEach(function(dom,i){
    var domData=ind[dom.id];
    var angle=(i/7)*Math.PI*2-Math.PI/2;
    var petalR=r*0.38;
    var petalDist=r+petalR+3;
    var px=cx+Math.cos(angle)*petalDist;
    var py=cy+Math.sin(angle)*petalDist;
    var score=domData.score;
    var alerts=domData.alertCount;

    // Petal color: green=no alerts, yellow=only warns, red=has danger
    var col=alerts>0?'#ff4444':(domData.indicators.some(function(x){return x.status==='warn';}))?'#ffbb33':'#33ffbe';
    var alpha=isHover||isSel?0.6:0.3;

    // Petal circle
    ctx.beginPath();ctx.arc(px,py,petalR,0,Math.PI*2);
    ctx.fillStyle=col.replace('#','rgba(').replace(/(..)(..)(..)$/,function(_,r,g,b){
      return parseInt(r,16)+','+parseInt(g,16)+','+parseInt(b,16)+','+alpha+')';
    });
    // Simpler: use hex to rgba
    var cr=parseInt(col.slice(1,3),16),cg=parseInt(col.slice(3,5),16),cb=parseInt(col.slice(5,7),16);
    ctx.fillStyle='rgba('+cr+','+cg+','+cb+','+alpha+')';
    ctx.fill();
    ctx.strokeStyle='rgba('+cr+','+cg+','+cb+','+(isHover||isSel?0.8:0.4)+')';
    ctx.lineWidth=alerts>0?1.5:0.8;
    ctx.stroke();

    // Alert badge
    if(alerts>0){
      ctx.beginPath();ctx.arc(px+petalR*0.6,py-petalR*0.6,4,0,Math.PI*2);
      ctx.fillStyle='#ff2020';ctx.fill();
      ctx.font='bold 5px Share Tech Mono';ctx.fillStyle='#fff';
      ctx.textAlign='center';ctx.textBaseline='middle';
      ctx.fillText(alerts>9?'9+':alerts,px+petalR*0.6,py-petalR*0.6);
    }

    // Domain initial
    if(petalR>=6){
      ctx.font=(isHover?'bold ':'')+Math.max(8,petalR*0.75)+'px Share Tech Mono';
      ctx.fillStyle='rgba('+cr+','+cg+','+cb+','+(isHover?1:0.85)+')';
      ctx.textAlign='center';ctx.textBaseline='middle';
      ctx.fillText(dom.icon,px,py);
    }
  });
}

// ── 绘制图谱
function drawGraph(){
  var canvas=document.getElementById('graph-canvas');if(!canvas)return;
  var ctx=canvas.getContext('2d');ctx.clearRect(0,0,canvasW,canvasH);

  // Grid
  ctx.strokeStyle='rgba(0,100,165,.05)';ctx.lineWidth=0.5;
  for(var gx=0;gx<canvasW;gx+=50){ctx.beginPath();ctx.moveTo(gx,0);ctx.lineTo(gx,canvasH);ctx.stroke();}
  for(var gy=0;gy<canvasH;gy+=50){ctx.beginPath();ctx.moveTo(0,gy);ctx.lineTo(canvasW,gy);ctx.stroke();}

  // Edges
  graphEdges.forEach(function(e){
    var src=graphNodes.find(function(n){return n.id===e.source;});
    var tgt=graphNodes.find(function(n){return n.id===e.target;});
    if(!src||!tgt)return;
    var rel=REL_TYPES[e.type]||REL_TYPES['hasSubsidiary'];
    var isHL=(hoveredNodeId&&(e.source===hoveredNodeId||e.target===hoveredNodeId));
    var mx=(src.x+tgt.x)/2,my=(src.y+tgt.y)/2;
    var dx=tgt.x-src.x,dy=tgt.y-src.y;
    var nx=-dy*0.12,ny=dx*0.12;
    ctx.beginPath();ctx.moveTo(src.x,src.y);ctx.quadraticCurveTo(mx+nx,my+ny,tgt.x,tgt.y);
    ctx.strokeStyle=isHL?rel.color.replace(/[\d.]+\)$/,'0.75)'):rel.color;
    ctx.lineWidth=isHL?2:1;ctx.setLineDash(rel.dash);ctx.stroke();ctx.setLineDash([]);
    // Arrow
    var t=0.82;
    var ax=(1-t)*(1-t)*src.x+2*(1-t)*t*(mx+nx)+t*t*tgt.x;
    var ay=(1-t)*(1-t)*src.y+2*(1-t)*t*(my+ny)+t*t*tgt.y;
    var t2=0.80;
    var bx=(1-t2)*(1-t2)*src.x+2*(1-t2)*t2*(mx+nx)+t2*t2*tgt.x;
    var by=(1-t2)*(1-t2)*src.y+2*(1-t2)*t2*(my+ny)+t2*t2*tgt.y;
    var aA=Math.atan2(ay-by,ax-bx);
    ctx.beginPath();ctx.moveTo(ax,ay);ctx.lineTo(ax-Math.cos(aA-0.4)*6,ay-Math.sin(aA-0.4)*6);ctx.lineTo(ax-Math.cos(aA+0.4)*6,ay-Math.sin(aA+0.4)*6);ctx.closePath();
    ctx.fillStyle=isHL?rel.color.replace(/[\d.]+\)$/,'0.75)'):rel.color;ctx.fill();
    if(isHL){ctx.font='10px Noto Sans SC';ctx.fillStyle=rel.color.replace(/[\d.]+\)$/,'0.95)');ctx.textAlign='center';ctx.fillText(rel.label,mx+nx*0.5,my+ny*0.5);}
  });

  // Nodes
  graphNodes.forEach(function(gn){
    var d=gn.data,col=riskColor(d.risk),glow=riskGlow(d.risk);
    var isHover=(hoveredNodeId===gn.id),isSel=(selectedNodeId===gn.id);
    var hasKids=d.children&&d.children.length;

    // Outer glow
    var grad=ctx.createRadialGradient(gn.x,gn.y,0,gn.x,gn.y,gn.r*2.5);
    grad.addColorStop(0,glow+(isHover?0.15:0.06)+')');grad.addColorStop(1,glow+'0)');
    ctx.fillStyle=grad;ctx.beginPath();ctx.arc(gn.x,gn.y,gn.r*2.5,0,Math.PI*2);ctx.fill();

    // Main circle
    ctx.beginPath();ctx.arc(gn.x,gn.y,gn.r,0,Math.PI*2);
    ctx.fillStyle=glow+(isHover?0.25:gn.isCenter?0.2:0.12)+')';ctx.fill();
    ctx.strokeStyle=glow+(isHover||isSel?0.85:0.45)+')';ctx.lineWidth=isSel?2.5:isHover?2:1;ctx.stroke();

    // Selection ring
    if(isSel){ctx.beginPath();ctx.arc(gn.x,gn.y,gn.r+5,0,Math.PI*2);ctx.strokeStyle=glow+'0.25)';ctx.lineWidth=1;ctx.stroke();}

    // High risk pulse
    if(d.risk==='hi'&&!gn.isCenter){
      var pulse=0.2+Math.sin(Date.now()/400)*0.15;
      ctx.beginPath();ctx.arc(gn.x,gn.y,gn.r+3,0,Math.PI*2);ctx.strokeStyle='rgba(255,32,32,'+pulse+')';ctx.lineWidth=1.5;ctx.stroke();
    }

    // Domain petals
    drawDomainPetals(ctx,gn);

    // Expand indicator
    if(hasKids&&!gn.isCenter){
      ctx.beginPath();ctx.arc(gn.x,gn.y-gn.r-2,5,0,Math.PI*2);ctx.fillStyle='rgba(0,216,255,0.15)';ctx.fill();ctx.strokeStyle='rgba(0,216,255,0.4)';ctx.lineWidth=0.8;ctx.stroke();
      ctx.font='bold 7px Share Tech Mono';ctx.fillStyle='#00d8ff';ctx.textAlign='center';ctx.textBaseline='middle';ctx.fillText('+',gn.x,gn.y-gn.r-2);
    }

    // Name + value
    ctx.font=(gn.isCenter?'600 14px':'11px')+' Noto Sans SC';ctx.fillStyle=isHover||isSel?'#fff':col;
    ctx.textAlign='center';ctx.textBaseline='middle';
    ctx.fillText(d.name.length>5?d.name.substring(0,5)+'..':d.name,gn.x,gn.y-3);
    ctx.font='9px Share Tech Mono';ctx.fillStyle=isHover?'rgba(255,255,255,0.8)':'rgba(140,200,224,0.7)';
    ctx.fillText(fmtMoney(d.asset),gn.x,gn.y+8);
  });

  // Legend
  var lx=10,ly=canvasH-100;
  ctx.font='10px Noto Sans SC';ctx.textAlign='left';
  // Relation legend
  Object.keys(REL_TYPES).forEach(function(k,i){
    var rel=REL_TYPES[k];ctx.beginPath();ctx.moveTo(lx,ly+i*15);ctx.lineTo(lx+20,ly+i*15);
    ctx.strokeStyle=rel.color;ctx.lineWidth=2;ctx.setLineDash(rel.dash);ctx.stroke();ctx.setLineDash([]);
    ctx.fillStyle=rel.color.replace(/[\d.]+\)$/,'0.85)');ctx.fillText(rel.label,lx+24,ly+i*15+4);
  });
  // Domain legend
  var dx=canvasW-160,dy=canvasH-100;
  ctx.font='10px Noto Sans SC';
  DOMAINS.forEach(function(dom,i){
    ctx.beginPath();ctx.arc(dx,dy+i*15,4,0,Math.PI*2);ctx.fillStyle=dom.color;ctx.fill();
    ctx.fillStyle='rgba(140,200,224,0.8)';ctx.fillText(dom.icon+' '+dom.name,dx+9,dy+i*15+4);
  });
}

// ── 面包屑
function renderBreadcrumb(){
  var el=document.getElementById('breadcrumb');if(!el)return;
  var h='';drillPath.forEach(function(node,i){
    if(i>0)h+='<span class="bc-sep"> \u25b6 </span>';
    h+='<span class="bc-item'+(i===drillPath.length-1?' bc-active':'')+'" onclick="drillTo('+i+')">'+node.name+'</span>';
  });el.innerHTML=h;
}
function drillTo(idx){drillPath=drillPath.slice(0,idx+1);currentNode=drillPath[idx];selectedNodeId=null;expandedDomains={};renderAll();}
function drillInto(node){if(!node||!node.children||!node.children.length)return;drillPath.push(node);currentNode=node;selectedNodeId=null;expandedDomains={};renderAll();}

// ── KPI
function renderKPI(){
  var n=currentNode;
  var all=flatAll(n);var totalAsset=sumField(n,'asset')||n.asset;var totalDebt=sumField(n,'debt')||n.debt;
  var totalCash=sumField(n,'cash')||n.cash;var totalGuar=sumField(n,'guarantee')||n.guarantee;
  var avgComp=0;all.forEach(function(x){avgComp+=x.compliance;});avgComp/=all.length;
  var hiRisk=all.filter(function(x){return x.risk==='hi';}).length;
  var debtRatio=totalAsset?(totalDebt/totalAsset*100).toFixed(1):'0';
  // Count total alerts across all domains for all entities
  var totalAlerts=0;all.forEach(function(x){var ind=generateIndicators(x);DOMAINS.forEach(function(dom){totalAlerts+=ind[dom.id].alertCount;});});

  var kpis=[
    {label:'\u73b0\u91d1\u603b\u989d',val:fmtMoney(totalCash),cls:'g',delta:'\u5b9e\u65f6\u5f52\u96c6'},
    {label:'\u8d44\u4ea7\u89c4\u6a21',val:fmtMoney(totalAsset),cls:'b',delta:'L'+(n.level+1)+' \u5c42\u7ea7'},
    {label:'\u8d1f\u503a\u7387',val:debtRatio+'%',cls:debtRatio>55?'r':'w',delta:fmtMoney(totalDebt)+'\u6709\u606f\u8d1f\u503a'},
    {label:'\u62c5\u4fdd\u4f59\u989d',val:fmtMoney(totalGuar),cls:totalGuar>1000000?'r':'a',delta:totalGuar>1000000?'\u26a0 \u8d85\u9650':'\u6b63\u5e38'},
    {label:'\u6307\u6807\u5f02\u5e38',val:totalAlerts+'\u9879',cls:totalAlerts>20?'r':totalAlerts>5?'w':'g',delta:'7\u00d7'+DOMAINS[0].indicators.length+' = 106\u6307\u6807'},
    {label:'\u5408\u89c4\u8bc4\u5206',val:avgComp.toFixed(1),cls:avgComp>=85?'go':avgComp>=70?'a':'r',delta:hiRisk>0?'\u26a0 '+hiRisk+'\u4e2a\u9ad8\u98ce\u9669':'\u5168\u90e8\u8fbe\u6807'},
  ];
  document.getElementById('kpi-bar').innerHTML=kpis.map(function(k){return '<div class="kpi"><div class="kpi-label">'+k.label+'</div><div class="kpi-val '+k.cls+'">'+k.val+'</div><div class="kpi-delta">'+k.delta+'</div></div>';}).join('');
}

// ── 左侧树
function buildTree(){
  var tree=document.getElementById('tree');if(!tree)return;tree.innerHTML='';
  var n=currentNode;
  if(!n.children||!n.children.length){tree.innerHTML='<div class="tgrp" style="padding:20px 11px;text-align:center;line-height:1.8">\u672b\u7ea7\u5355\u4f4d</div>';return;}
  var groups=[{label:'\u26a0 \u9ad8\u98ce\u9669',fn:function(c){return c.risk==='hi';}},{label:'\u25b2 \u4e2d\u98ce\u9669',fn:function(c){return c.risk==='md';}},{label:'\u25cf \u6b63\u5e38',fn:function(c){return c.risk==='lo';}}];
  groups.forEach(function(g){
    var ents=n.children.filter(g.fn);if(!ents.length)return;
    var gl=document.createElement('div');gl.className='tgrp';gl.innerHTML=g.label+' ('+ents.length+')';tree.appendChild(gl);
    ents.forEach(function(e){
      var el=document.createElement('div');el.className='titem'+(e.risk==='hi'?' br':'')+(selectedNodeId===e.id?' sel':'');el.id='ti-'+e.id;
      var dotCls=e.risk==='hi'?'dr':e.risk==='md'?'da':'dc';
      var ind=generateIndicators(e);var redCount=0,yellowCount=0;DOMAINS.forEach(function(dom){ind[dom.id].indicators.forEach(function(x){if(x.status==='danger')redCount++;if(x.status==='warn')yellowCount++;});});
      var hasKids=e.children&&e.children.length;
      var tagHtml=redCount>0?'<span style="color:var(--danger);font-weight:600">'+redCount+'\u7ea2</span>':(yellowCount>0?'<span style="color:var(--warn)">'+yellowCount+'\u9ec4</span>':'<span style="color:var(--a2)">\u7eff</span>');
      el.innerHTML='<div class="tdot '+dotCls+'"></div><div class="tlbl">'+e.name+(hasKids?' \u25b6':'')+'</div><div class="ttag">'+tagHtml+'</div><div class="trsk r'+e.risk+'">'+(e.risk==='hi'?'\u9ad8':e.risk==='md'?'\u4e2d':'\u4f4e')+'</div>';
      el.onclick=function(){selectedNodeId=e.id;expandedDomains={};renderDetail(e);buildTree();};
      el.ondblclick=function(){if(hasKids)drillInto(e);};
      tree.appendChild(el);
    });
  });
  var tc=document.getElementById('tree-count');if(tc)tc.textContent=n.children.length+' \u5b9e\u4f53';
}
function filterTree(v){v=v.toLowerCase();document.querySelectorAll('.titem').forEach(function(el){var l=(el.querySelector('.tlbl')||{}).textContent||'';el.style.display=(!v||l.toLowerCase().indexOf(v)>=0)?'':'none';});}

// ── 右侧详情：7大领域 + 指标明细
function renderDetail(node){
  var n=node||currentNode;
  var ind=generateIndicators(n);
  var ib=n.risk==='hi';

  var h='<div class="dsec"><div class="dlbl">'+n.type+' \u00b7 L'+(n.level+1)+' \u00b7 '+n.city+'</div>';
  h+='<div class="dtitle'+(ib?' br':'')+'">'+n.name+'</div></div>';

  // 7 Domain panels
  DOMAINS.forEach(function(dom){
    var dd=ind[dom.id];
    var isExpanded=expandedDomains[dom.id];
    var scoreColor=dangerCount===0&&warnCount===0?'var(--a2)':dangerCount>0?'var(--danger)':'var(--warn)';
    var dangerCount=dd.indicators.filter(function(x){return x.status==='danger';}).length;
    var warnCount=dd.indicators.filter(function(x){return x.status==='warn';}).length;

    h+='<div class="dom-panel" style="border-bottom:1px solid var(--b1)">';
    h+='<div class="dom-head" onclick="toggleDomain(\''+dom.id+'\')" style="padding:5px 11px;display:flex;align-items:center;gap:6px;cursor:pointer;transition:background .1s;'+(isExpanded?'background:rgba(0,216,255,.03)':'')+'">';
    h+='<div style="width:8px;height:8px;border-radius:50%;background:'+dom.color+';box-shadow:0 0 6px '+dom.color+';flex-shrink:0"></div>';
    h+='<div style="font-size:12px;font-weight:600;color:'+dom.color+';flex:1">'+dom.name+'</div>';
    if(dangerCount>0) h+='<div style="font-family:var(--mono);font-size:9px;color:var(--danger);border:1px solid var(--danger);padding:1px 4px;font-weight:600">'+dangerCount+'\u7ea2</div>';
    if(warnCount>0) h+='<div style="font-family:var(--mono);font-size:9px;color:var(--warn);border:1px solid rgba(255,187,51,.5);padding:1px 4px">'+warnCount+'\u9ec4</div>';
    var okCount=dd.indicators.length-dangerCount-warnCount;
    h+='<div style="font-family:var(--mono);font-size:9px;color:var(--a2);opacity:.6">'+okCount+'\u7eff</div>';
    h+='<div style="font-family:var(--orb);font-size:12px;font-weight:600;color:'+scoreColor+'">'+dd.score+'</div>';
    h+='<div style="width:50px;height:4px;background:var(--b2);border-radius:2px"><div style="width:'+dd.score+'%;height:4px;background:'+scoreColor+';border-radius:2px"></div></div>';
    h+='<div style="font-size:9px;color:var(--text)">'+(isExpanded?'\u25b2':'\u25bc')+'</div>';
    h+='</div>';

    if(isExpanded){
      h+='<div style="padding:0 11px 6px">';
      // Sort: danger first, then warn, then normal
      var sorted=dd.indicators.slice().sort(function(a,b){var o={danger:0,warn:1,normal:2};return(o[a.status]||2)-(o[b.status]||2);});
      sorted.forEach(function(indicator){
        var ic=indicator.status==='danger'?'var(--danger)':indicator.status==='warn'?'var(--warn)':'var(--a2)';
        var bg=indicator.status==='danger'?'rgba(255,68,68,.06)':indicator.status==='warn'?'rgba(255,187,51,.05)':'transparent';
        var badge=indicator.status==='danger'?'<span style="font-family:var(--mono);font-size:8px;color:var(--danger);border:1px solid var(--danger);padding:0 3px;margin-left:4px;font-weight:600">\u7ea2</span>':(indicator.status==='warn'?'<span style="font-family:var(--mono);font-size:8px;color:var(--warn);border:1px solid rgba(255,187,51,.5);padding:0 3px;margin-left:4px">\u9ec4</span>':'<span style="font-family:var(--mono);font-size:8px;color:var(--a2);border:1px solid rgba(51,255,190,.3);padding:0 3px;margin-left:4px">\u7eff</span>');
        h+='<div style="display:flex;justify-content:space-between;align-items:center;padding:3px 0;border-bottom:1px solid rgba(12,32,56,.4);background:'+bg+'">';
        h+='<span style="font-size:10px;color:'+ic+'">'+indicator.name+badge+'</span>';
        h+='<span style="font-family:var(--mono);font-size:10px;color:'+ic+';font-weight:600">'+indicator.value+(indicator.unit?' '+indicator.unit:'')+'</span>';
        h+='</div>';
      });
      h+='</div>';
    }
    h+='</div>';
  });

  // Actions
  var hasKids=n.children&&n.children.length;
  h+='<div class="arow">';
  if(hasKids) h+='<button class="abtn g" onclick="drillInto(findNode(\''+n.id+'\'))">\u94bb\u5165\u4e0b\u7ea7</button>';
  h+='<button class="abtn g" onclick="expandAllDomains()">\u5c55\u5f00\u5168\u90e8</button>';
  h+='<button class="abtn w" onclick="doAct(\'\u98ce\u9669\u62a5\u544a\')">\u98ce\u9669\u62a5\u544a</button>';
  h+='<button class="abtn g" onclick="doAct(\'\u5bfc\u51fa\')">\u5bfc\u51fa</button>';
  h+='</div>';

  document.getElementById('rs').innerHTML=h;
}

function toggleDomain(domId){
  expandedDomains[domId]=!expandedDomains[domId];
  var node=selectedNodeId?findNode(selectedNodeId):currentNode;
  renderDetail(node);
}
function expandAllDomains(){
  DOMAINS.forEach(function(d){expandedDomains[d.id]=true;});
  var node=selectedNodeId?findNode(selectedNodeId):currentNode;
  renderDetail(node);
}
function doAct(name){var n=document.getElementById('notif');n.textContent='\u25b6 '+name+' \u2014 \u6267\u884c\u4e2d...';n.style.display='block';setTimeout(function(){n.style.display='none';},1600);}

// ── Ticker + Clock
function buildTicker(){
  var tickers=[{n:'USD/CNY',v:'7.2618',d:'+0.0021',u:true},{n:'EUR/CNY',v:'7.8642',d:'-0.0034',u:false},{n:'SHIBOR',v:'2.42%',d:'-0.01',u:false},{n:'LPR',v:'3.45%',d:'0.00',u:null},{n:'\u56fd\u503a10Y',v:'2.68%',d:'-0.02',u:false},{n:'\u6caa\u6df1300',v:'3842',d:'+28',u:true},{n:'DR007',v:'1.82%',d:'+0.03',u:true},{n:'GOLD',v:'$2198',d:'+12',u:true}];
  var h=tickers.map(function(t){var cls=t.u===true?'tku':t.u===false?'tkd':'';var a=t.u===true?'\u25b2':t.u===false?'\u25bc':'\u2500';return '<span class="tk"><span class="tkn">'+t.n+'</span><span class="'+cls+'">'+t.v+' '+a+' '+t.d+'</span></span>';}).join('');
  document.getElementById('ticker').innerHTML=h+h;
}
function tickClock(){var now=new Date();var bj=new Date(now.getTime()+8*3600000);var hh=('0'+bj.getUTCHours()).slice(-2);var mm=('0'+bj.getUTCMinutes()).slice(-2);var ss=('0'+bj.getUTCSeconds()).slice(-2);document.getElementById('clock').textContent=hh+':'+mm+':'+ss;document.getElementById('sbtime').textContent=hh+':'+mm;}

// ── Canvas events
function setupGraphEvents(){
  var canvas=document.getElementById('graph-canvas');if(!canvas)return;
  function getNodeAt(mx,my){var rect=canvas.getBoundingClientRect();var x=mx-rect.left,y=my-rect.top;for(var i=graphNodes.length-1;i>=0;i--){var gn=graphNodes[i];var dx=x-gn.x,dy=y-gn.y;var hitR=gn.r+gn.r*0.5;if(dx*dx+dy*dy<=hitR*hitR)return gn;}return null;}
  canvas.addEventListener('mousemove',function(ev){
    if(dragNode){var rect=canvas.getBoundingClientRect();dragNode.x=ev.clientX-rect.left-dragOffX;dragNode.y=ev.clientY-rect.top-dragOffY;dragNode.fixed=true;return;}
    var gn=getNodeAt(ev.clientX,ev.clientY);hoveredNodeId=gn?gn.id:null;canvas.style.cursor=gn?'pointer':'default';
    var tip=document.getElementById('graph-tip');
    if(gn&&tip){tip.style.display='block';var rect=canvas.getBoundingClientRect();tip.style.left=(ev.clientX-rect.left+14)+'px';tip.style.top=(ev.clientY-rect.top-10)+'px';
      var d=gn.data;var ind=generateIndicators(d);var alerts=0;DOMAINS.forEach(function(dom){alerts+=ind[dom.id].alertCount;});
      tip.innerHTML='<b>'+d.name+'</b><br>'+d.type+' \u00b7 '+d.city+' \u00b7 '+riskLabel(d.risk)+'<br>\u8d44\u4ea7: '+fmtMoney(d.asset)+' \u00b7 \u73b0\u91d1: '+fmtMoney(d.cash)+(alerts>0?'<br><span style="color:#ff2020">\u26a0 '+alerts+'\u9879\u6307\u6807\u5f02\u5e38</span>':'')+(d.children&&d.children.length?'<br><span style="color:#00d8ff">\u53cc\u51fb\u94bb\u5165 ('+d.children.length+'\u4e2a\u4e0b\u7ea7)</span>':'');
    }else if(tip){tip.style.display='none';}
  });
  canvas.addEventListener('mousedown',function(ev){var gn=getNodeAt(ev.clientX,ev.clientY);if(gn&&!gn.isCenter){dragNode=gn;var rect=canvas.getBoundingClientRect();dragOffX=ev.clientX-rect.left-gn.x;dragOffY=ev.clientY-rect.top-gn.y;}});
  canvas.addEventListener('mouseup',function(){if(dragNode){dragNode.fixed=false;dragNode=null;}});
  canvas.addEventListener('click',function(ev){var gn=getNodeAt(ev.clientX,ev.clientY);if(gn){selectedNodeId=gn.id;expandedDomains={};renderDetail(gn.data);buildTree();}});
  canvas.addEventListener('dblclick',function(ev){var gn=getNodeAt(ev.clientX,ev.clientY);if(gn&&gn.data.children&&gn.data.children.length)drillInto(gn.data);});
  canvas.addEventListener('mouseleave',function(){hoveredNodeId=null;dragNode=null;var tip=document.getElementById('graph-tip');if(tip)tip.style.display='none';});
}

// ── Render + Animate
function renderAll(){
  var canvas=document.getElementById('graph-canvas');
  if(canvas){var rect=canvas.parentElement.getBoundingClientRect();canvasW=rect.width;canvasH=rect.height;canvas.width=canvasW;canvas.height=canvasH;}
  renderBreadcrumb();renderKPI();buildTree();buildGraphData();renderDetail(currentNode);
}
function animate(){simStep();drawGraph();requestAnimationFrame(animate);}
window.addEventListener('resize',function(){clearTimeout(window._rt);window._rt=setTimeout(function(){var canvas=document.getElementById('graph-canvas');if(canvas){var rect=canvas.parentElement.getBoundingClientRect();canvasW=rect.width;canvasH=rect.height;canvas.width=canvasW;canvas.height=canvasH;}buildGraphData();},150);});
window.addEventListener('load',function(){buildTicker();setInterval(tickClock,1000);tickClock();renderAll();setupGraphEvents();animate();});
