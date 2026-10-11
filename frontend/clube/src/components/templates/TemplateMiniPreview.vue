<template>
  <div :style="rootStyle">

    <!-- ── CLÁSSICO ── -->
    <template v-if="id === 'classico'">
      <div :style="abs({ background:'repeating-linear-gradient(135deg,rgba(255,255,255,0.04) 0,rgba(255,255,255,0.04) 10px,rgba(255,255,255,0.01) 10px,rgba(255,255,255,0.01) 20px)' })"></div>
      <div :style="abs({ background:'rgba(9,9,11,0.55)' })"></div>
      <div :style="abs({ background:'linear-gradient(to top,#09090b,rgba(9,9,11,0.4) 55%,transparent)' })"></div>
      <div :style="abs({ top:'7px', left:'7px', inset:'auto', width:'18px', height:'18px', borderRadius:'50%', background:'rgba(0,0,0,0.5)', display:'flex', alignItems:'center', justifyContent:'center' })">
        <span style="color:#fff;font-size:8px">←</span>
      </div>
      <div :style="abs({ bottom:'42%', left:'8px', inset:'auto', display:'flex', alignItems:'flex-end', gap:'5px' })">
        <div :style="{ width:'24px', height:'24px', borderRadius:'5px', background:primary, display:'flex', alignItems:'center', justifyContent:'center', fontSize:'11px', fontWeight:'900', color:'#fff', flexShrink:'0' }">A</div>
        <div>
          <div :style="{ fontSize:'4px', color:primary, fontWeight:'700', letterSpacing:'0.1em', textTransform:'uppercase' }">Moda</div>
          <div style="font-size:9px;font-weight:800;color:#fff;line-height:1.1">Armazém Geral</div>
          <div style="font-size:4px;color:#a1a1aa;margin-top:1px">Lisboa · 4.8</div>
        </div>
      </div>
      <div :style="abs({ bottom:'20%', left:'8px', right:'8px', inset:'auto', display:'grid', gridTemplateColumns:'2fr 1fr', gap:'3px' })">
        <div style="background:#18181b;border:1px solid #27272a;border-radius:4px;padding:3px 5px">
          <div style="font-size:3px;color:#52525b;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:1px">Sobre</div>
          <div style="font-size:4px;color:#71717a;line-height:1.3">Curadoria de peças únicas para quem valoriza o detalhe.</div>
        </div>
        <div style="background:#18181b;border:1px solid #27272a;border-radius:4px;padding:3px 5px">
          <div style="font-size:3px;color:#52525b;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:1px">Entrega</div>
          <div style="font-size:5px;color:#4ade80;font-weight:600">Grátis</div>
        </div>
      </div>
      <div :style="abs({ bottom:'4%', left:'8px', right:'8px', inset:'auto' })">
        <div style="font-size:5px;font-weight:700;color:#71717a;margin-bottom:2px">Em Destaque</div>
        <div style="display:flex;gap:3px">
          <div v-for="i in 4" :key="i" style="flex-shrink:0;width:42px;background:#18181b;border:1px solid #27272a;border-radius:4px;overflow:hidden">
            <div style="height:22px;position:relative;background:repeating-linear-gradient(135deg,rgba(255,255,255,0.04) 0,rgba(255,255,255,0.04) 10px,rgba(255,255,255,0.01) 10px,rgba(255,255,255,0.01) 20px)"></div>
            <div style="padding:2px 3px">
              <div style="font-size:3.5px;color:#e4e4e7;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">Produto</div>
              <div :style="{ fontSize:'3.5px', color:primary, fontWeight:'700' }">89,90€</div>
            </div>
          </div>
        </div>
      </div>
    </template>

    <!-- ── MINIMALISTA ── -->
    <template v-else-if="id === 'minimalista'">
      <!-- papel claro, barra de texto, nome leve à esquerda e banner emoldurado à direita -->
      <div :style="abs({ background:'#f4f2ee' })"></div>
      <div style="position:absolute;top:6px;left:9px;display:flex;gap:6px;font-size:4px;color:#161514">
        <span>Voltar</span><span style="color:#9a958c">|</span><span>Escuro</span>
      </div>
      <div style="position:absolute;left:9px;bottom:14px;width:52%;color:#161514">
        <div style="font-size:3.5px;letter-spacing:0.18em;text-transform:uppercase;color:#5f5b55;margin-bottom:5px">Moda · Lisboa</div>
        <div style="font-size:17px;font-weight:300;line-height:0.95;letter-spacing:-0.045em;margin-bottom:6px">Armazém Geral</div>
        <div style="display:flex;gap:9px;border-top:0.5px solid rgba(22,21,20,.15);padding-top:3px;margin-bottom:6px">
          <div v-for="([l,v]) in [['Avaliação','4.8'],['Entrega','Grátis'],['Peças','42']]" :key="l">
            <div style="font-size:2.5px;letter-spacing:0.14em;text-transform:uppercase;color:#9a958c">{{ l }}</div>
            <div style="font-size:5px">{{ v }}</div>
          </div>
        </div>
        <div style="display:inline-block;padding:2.5px 6px;background:#161514;color:#f4f2ee;font-size:3.5px;letter-spacing:0.06em;text-transform:uppercase">Ver a selecção</div>
      </div>
      <div style="position:absolute;right:9px;top:16px;bottom:12px;width:34%;background:#ebe8e2;padding:3px;box-shadow:inset 0 0 0 0.5px rgba(22,21,20,.12)">
        <div :style="{ width:'100%', height:'100%', background:'linear-gradient(160deg,'+primary+'55,#d8d3ca)' }"></div>
      </div>
      <div style="position:absolute;right:9px;bottom:5px;font-size:3px;color:#9a958c">Fig. 01</div>
    </template>

    <!-- ── MODA BOUTIQUE ── -->
    <template v-else-if="id === 'moda_boutique'">
      <div style="position:absolute;inset:0;background:#faf5f2"></div>
      <div style="position:absolute;top:5px;left:6px;display:flex;align-items:center;gap:2px">
        <div style="width:7px;height:7px;border-radius:50%;background:#fff;border:0.5px solid rgba(43,35,38,0.2)"></div>
        <div style="width:7px;height:7px;border-radius:50%;background:#fff;border:0.5px solid rgba(43,35,38,0.2)"></div>
        <span style="margin-left:3px;font-size:4.5px;letter-spacing:0.15em;color:#2b2326;font-family:Georgia,serif">ARMAZÉM</span>
      </div>
      <div :style="{ position:'absolute', top:'16px', left:'6px', right:'6px', height:'52%', borderRadius:'8px', overflow:'hidden', background:'linear-gradient(140deg,#e8d5d0,'+primary+')' }">
        <div style="position:absolute;inset:0;background:linear-gradient(to top,rgba(20,14,16,0.7),transparent 60%)"></div>
        <div style="position:absolute;left:7px;bottom:6px;color:#fff">
          <div style="font-size:3.5px;letter-spacing:0.25em;opacity:0.85">MODA · LISBOA</div>
          <div style="font-size:12px;letter-spacing:0.06em;line-height:1;margin:2px 0 3px;font-family:Georgia,serif">ARMAZÉM</div>
          <div style="display:inline-block;padding:1.5px 5px;border-radius:6px;background:#fff;color:#2b2326;font-size:3.2px;letter-spacing:0.15em">NOVIDADES</div>
        </div>
        <div style="position:absolute;top:6px;right:7px;padding:2px 4px 2px 7px;background:#fff;clip-path:polygon(3px 0,100% 0,100% 100%,3px 100%,0 50%);transform:rotate(-6deg)">
          <div style="font-size:2.8px;letter-spacing:0.15em;color:#7b6d70">COLEÇÃO</div>
          <div style="font-size:5px;color:#2b2326;font-family:Georgia,serif">24 peças</div>
        </div>
      </div>
      <div style="position:absolute;top:73%;left:0;right:0;height:7px;background:#1f1a1d;display:flex;align-items:center;justify-content:center;gap:5px">
        <span v-for="t in ['VESTIDOS','MALAS','JOIAS']" :key="t" style="font-size:3px;letter-spacing:0.2em;color:#f6eef0">{{ t }}</span>
      </div>
      <div style="position:absolute;bottom:4px;left:6px;right:6px;display:grid;grid-template-columns:repeat(4,1fr);gap:3px">
        <div v-for="i in 4" :key="i" style="position:relative;height:16px;border-radius:3px;background:linear-gradient(160deg,#efe2de,#d9c2bc)">
          <div style="position:absolute;top:2px;right:2px;width:6px;height:3px;background:#fff;clip-path:polygon(1.5px 0,100% 0,100% 100%,1.5px 100%,0 50%)"></div>
        </div>
      </div>
    </template>

    <!-- ── MODA EDITORIAL ── -->
    <template v-else-if="id === 'moda_editorial'">
      <div style="position:absolute;inset:0;display:grid;grid-template-columns:3fr 2fr">
        <div style="position:relative;overflow:hidden">
          <div style="position:absolute;inset:0;background:repeating-linear-gradient(135deg,rgba(255,255,255,0.04) 0,rgba(255,255,255,0.04) 10px,rgba(255,255,255,0.01) 10px,rgba(255,255,255,0.01) 20px)"></div>
          <div style="position:absolute;inset:0;background:rgba(9,9,11,0.25)"></div>
          <div style="position:absolute;bottom:-4px;left:6px;font-size:34px;font-weight:900;color:rgba(255,255,255,0.05);line-height:1;letter-spacing:-0.05em;user-select:none">2025</div>
          <div style="position:absolute;inset:0;background:linear-gradient(to right,transparent 55%,#09090b)"></div>
        </div>
        <div style="display:flex;flex-direction:column;justify-content:center;padding:12px 8px 12px 4px">
          <div :style="{ fontSize:'4px', letterSpacing:'0.5em', textTransform:'uppercase', color:primary, marginBottom:'5px' }">Moda</div>
          <div style="font-size:14px;font-weight:900;letter-spacing:-0.04em;line-height:0.9;color:#fafafa;margin-bottom:5px;word-break:break-word">Armazém Geral</div>
          <div style="display:flex;align-items:center;gap:3px;margin-bottom:5px">
            <div style="flex:1;height:0.5px;background:#27272a"></div>
            <div :style="{ width:'5px', height:'5px', transform:'rotate(45deg)', background:primary, flexShrink:'0' }"></div>
            <div style="flex:1;height:0.5px;background:#27272a"></div>
          </div>
          <div style="font-size:4px;color:#52525b;margin-bottom:5px;line-height:1.4">Curadoria exclusiva de peças.</div>
          <div :style="{ display:'inline-flex', padding:'3px 7px', background:primary, color:'#09090b', fontSize:'4px', fontWeight:'900', textTransform:'uppercase', alignSelf:'flex-start' }">Ver Coleção</div>
        </div>
      </div>
    </template>

    <!-- ── RESTAURANTE BISTRO ── -->
    <template v-else-if="id === 'restaurante_bistro'">
      <div style="position:absolute;inset:0;background:#f6efe2"></div>
      <div style="position:absolute;top:5px;left:6px;display:flex;gap:2px">
        <div style="width:7px;height:7px;border-radius:50%;background:#fbf7ef;border:0.5px solid rgba(42,33,27,0.25)"></div>
        <div style="width:7px;height:7px;border-radius:50%;background:#fbf7ef;border:0.5px solid rgba(42,33,27,0.25)"></div>
      </div>
      <div style="position:absolute;top:16px;left:6px;right:6px;height:50%;background:#fbf7ef;border:0.5px solid rgba(42,33,27,0.2);display:grid;grid-template-columns:1.2fr 0.8fr;align-items:center;gap:4px;padding:5px">
        <div style="position:absolute;inset:2px;border:0.5px solid rgba(42,33,27,0.2);pointer-events:none"></div>
        <div style="text-align:center">
          <div :style="{ fontSize:'3.5px', fontWeight:'700', letterSpacing:'0.2em', textTransform:'uppercase', color:primary }">Bistrô · Lisboa</div>
          <div style="font-size:13px;font-style:italic;font-weight:600;color:#2a211b;line-height:0.95;margin:2px 0;font-family:Georgia,serif">Armazém Geral</div>
          <div style="display:flex;align-items:center;justify-content:center;gap:3px">
            <div :style="{ width:'10px', height:'0.5px', background:primary }"></div>
            <div :style="{ width:'2.5px', height:'2.5px', transform:'rotate(45deg)', border:'0.5px solid '+primary }"></div>
            <div :style="{ width:'10px', height:'0.5px', background:primary }"></div>
          </div>
          <div :style="{ display:'inline-block', marginTop:'4px', padding:'2px 6px', borderRadius:'6px', background:primary, color:'#fff', fontSize:'3.8px', fontWeight:'700' }">Ver a carta</div>
        </div>
        <div style="height:92%;border-radius:20px 20px 1px 1px;background:linear-gradient(160deg,#c9a77c,#7a5638)"></div>
      </div>
      <div style="position:absolute;bottom:6px;left:12px;right:12px;height:26%;background:#1e2a24;border:2.5px solid #6b4e35;border-radius:2px;padding:3px 6px">
        <div style="text-align:center;font-family:'Comic Sans MS',cursive;font-size:5.5px;color:#f4f1ea;margin-bottom:2px">Sugestões do chef</div>
        <div v-for="i in 3" :key="i" style="display:flex;align-items:flex-end;gap:2px;margin-top:1.5px">
          <div style="width:24px;height:1.5px;background:rgba(244,241,234,0.8)"></div>
          <div style="flex:1;border-bottom:0.5px dotted rgba(244,241,234,0.4)"></div>
          <div style="width:7px;height:1.5px;background:rgba(244,241,234,0.8)"></div>
        </div>
      </div>
    </template>

    <!-- ── RESTAURANTE MODERNO ── -->
    <template v-else-if="id === 'restaurante_moderno'">
      <!-- foto do hero -->
      <div :style="{ position:'absolute', inset:'0', background:'radial-gradient(circle at 72% 28%,'+primary+'88,transparent 55%),radial-gradient(circle at 18% 85%,'+primary+'40,transparent 50%),#1a1512' }"></div>
      <div style="position:absolute;inset:0;background:linear-gradient(to top,rgba(12,9,7,.92),rgba(12,9,7,.3) 55%,rgba(12,9,7,.2)),linear-gradient(to right,rgba(12,9,7,.5),transparent 60%)"></div>
      <!-- top bar -->
      <div style="position:absolute;top:6px;left:8px;right:8px;display:flex;align-items:center;gap:4px">
        <div :style="{ width:'9px', height:'9px', borderRadius:'50%', background:primary, fontSize:'5px', fontWeight:'800', display:'flex', alignItems:'center', justifyContent:'center', fontFamily:'Georgia,serif' }">A</div>
        <span style="font-size:5px;font-weight:600;font-family:Georgia,serif">Armazém</span>
        <div style="margin-left:auto;display:flex;gap:5px;font-size:3.5px;color:rgba(255,255,255,.7)"><span>Chef</span><span>Carta</span><span>Visite-nos</span></div>
      </div>
      <!-- copy -->
      <div style="position:absolute;bottom:11px;left:9px;width:58%">
        <div style="display:flex;gap:2px;margin-bottom:4px">
          <span :style="{ padding:'1.5px 4px', borderRadius:'6px', background:primary, fontSize:'3.5px', fontWeight:'700' }">Restaurante</span>
          <span style="padding:1.5px 4px;border-radius:6px;background:rgba(255,255,255,.14);font-size:3.5px">Lisboa</span>
        </div>
        <div style="font-size:18px;font-weight:800;letter-spacing:-0.03em;line-height:0.92;font-family:Georgia,serif;margin-bottom:4px">Armazém Geral</div>
        <div style="font-size:3.8px;color:rgba(255,255,255,.7);margin-bottom:5px;line-height:1.4">Cozinha de autor com produtos da época.</div>
        <div style="display:flex;gap:3px">
          <div :style="{ padding:'3px 7px', borderRadius:'8px', background:primary, fontSize:'4px', fontWeight:'700' }">Ver a carta ↓</div>
          <div style="padding:3px 7px;border-radius:8px;background:rgba(255,255,255,.12);border:0.5px solid rgba(255,255,255,.25);font-size:4px;font-weight:700">Sugestões do chef</div>
        </div>
      </div>
      <!-- cartão de serviço -->
      <div style="position:absolute;bottom:11px;right:9px;width:30%;padding:5px 6px;border-radius:6px;background:rgba(20,16,13,.6);border:0.5px solid rgba(255,255,255,.15)">
        <div style="font-size:3px;letter-spacing:0.18em;text-transform:uppercase;color:rgba(255,255,255,.5);margin-bottom:2px">Serviço</div>
        <div v-for="([l,v]) in [['Entrega','desde 0€'],['Take-away','Sim'],['Pratos','42']]" :key="l"
             style="display:flex;justify-content:space-between;padding:2px 0;border-bottom:0.5px solid rgba(255,255,255,.1);font-size:3.5px">
          <span style="color:rgba(255,255,255,.7)">{{ l }}</span><span style="font-weight:700">{{ v }}</span>
        </div>
        <div style="display:flex;align-items:center;gap:3px;margin-top:3px">
          <span style="font-size:11px;font-weight:800;font-family:Georgia,serif;line-height:1">4.8</span>
          <span :style="{ fontSize:'4px', color:primary }">★★★★★</span>
        </div>
      </div>
    </template>

    <!-- ── TECH STORE ── -->
    <template v-else-if="id === 'tech_store'">
      <div style="position:absolute;inset:0;background:#0b0f17;background-image:linear-gradient(rgba(238,242,248,0.05) 0.5px,transparent 0.5px),linear-gradient(90deg,rgba(238,242,248,0.05) 0.5px,transparent 0.5px);background-size:8px 8px"></div>
      <div :style="{ position:'absolute', right:'10%', top:'15%', width:'50%', height:'45%', borderRadius:'50%', background:primary, opacity:'0.18', filter:'blur(14px)' }"></div>
      <div style="position:absolute;top:5px;left:6px;display:flex;align-items:center;gap:2px">
        <div style="width:7px;height:7px;border-radius:2px;background:#151b26;border:0.5px solid rgba(238,242,248,0.15)"></div>
        <div style="width:7px;height:7px;border-radius:2px;background:#151b26;border:0.5px solid rgba(238,242,248,0.15)"></div>
        <span style="margin-left:3px;font-size:4.5px;font-weight:600;color:#eef2f8">Armazém</span>
      </div>
      <div style="position:absolute;top:19%;left:7px;width:48%">
        <div style="display:flex;align-items:center;gap:2px;font-size:3.2px;color:#8e98aa;letter-spacing:0.08em;font-family:monospace">
          <span :style="{ width:'3px', height:'3px', borderRadius:'50%', background:primary, display:'inline-block' }"></span>TECNOLOGIA / LISBOA
        </div>
        <div style="font-size:12px;font-weight:700;letter-spacing:-0.04em;line-height:1;color:#eef2f8;margin:3px 0 4px">Armazém</div>
        <div style="display:grid;grid-template-columns:1fr 1fr;border:0.5px solid rgba(238,242,248,0.12);border-radius:3px;background:#151b26">
          <div v-for="([l, v], i) in [['AVAL.','4.8'],['PROD.','124'],['ENTR.','Grátis'],['PAG.','3']]" :key="l"
               :style="{ padding:'2px 3px', borderRight: i % 2 === 0 ? '0.5px solid rgba(238,242,248,0.12)' : 'none', borderBottom: i < 2 ? '0.5px solid rgba(238,242,248,0.12)' : 'none' }">
            <div style="font-size:2.5px;color:#8e98aa;font-family:monospace">{{ l }}</div>
            <div style="font-size:5px;font-weight:600;color:#eef2f8">{{ v }}</div>
          </div>
        </div>
        <div :style="{ display:'inline-block', marginTop:'4px', padding:'2px 5px', borderRadius:'3px', background:primary, color:'#fff', fontSize:'3.6px', fontWeight:'600' }">Explorar produtos →</div>
      </div>
      <div style="position:absolute;top:20%;right:7px;width:38%;height:42%;padding:2px">
        <div v-for="c in [['top','left'],['top','right'],['bottom','left'],['bottom','right']]" :key="c.join()"
             :style="{ position:'absolute', [c[0]]:'0', [c[1]]:'0', width:'4px', height:'4px', ['border' + c[0][0].toUpperCase() + c[0].slice(1)]:'1px solid ' + primary, ['border' + c[1][0].toUpperCase() + c[1].slice(1)]:'1px solid ' + primary }"></div>
        <div style="width:100%;height:100%;border-radius:4px;background:linear-gradient(150deg,#1d2533,#2a3550);border:0.5px solid rgba(238,242,248,0.12)"></div>
      </div>
      <div style="position:absolute;bottom:5px;left:7px;right:7px;display:grid;grid-template-columns:repeat(4,1fr);gap:3px">
        <div v-for="i in 4" :key="i" style="height:22px;border-radius:3px;background:#151b26;border:0.5px solid rgba(238,242,248,0.1);overflow:hidden">
          <div style="height:12px;background:#1d2533"></div>
          <div style="margin:2px 2px 0;height:1.5px;width:70%;background:rgba(238,242,248,0.5)"></div>
          <div style="margin:2px 2px 0;height:1.5px;width:40%;background:rgba(238,242,248,0.25)"></div>
        </div>
      </div>
    </template>

    <!-- ── VIBRANTE ── -->
    <template v-else-if="id === 'vibrante'">
      <div style="position:absolute;inset:0;background:#fff8ef"></div>
      <div style="position:absolute;top:5px;left:7px;display:flex;align-items:center;gap:3px;padding:2px;border-radius:10px;background:#fff;box-shadow:0 0 0 0.5px rgba(23,19,15,0.12)">
        <div style="width:7px;height:7px;border-radius:50%;background:#fff8ef"></div>
        <div :style="{ width:'6px', height:'6px', borderRadius:'50%', background:primary }"></div>
        <span style="font-size:4.5px;font-weight:800;color:#17130f">Armazém</span>
        <div style="width:7px;height:7px;border-radius:50%;background:#fff8ef"></div>
      </div>
      <div :style="{ position:'absolute', top:'17%', left:'7px', right:'7px', height:'50%', borderRadius:'12px', overflow:'hidden', background:primary }">
        <div style="position:absolute;width:70%;padding-bottom:70%;border-radius:50%;right:-22%;bottom:-55%;background:rgba(255,255,255,0.13)"></div>
        <div style="position:absolute;top:9px;left:8px">
          <div style="display:inline-block;padding:1px 4px;border-radius:6px;background:rgba(255,255,255,0.2);font-size:3.5px;font-weight:700;color:#fff">Moda</div>
          <div style="font-size:17px;font-weight:800;line-height:0.88;letter-spacing:-0.04em;color:#fff;margin-top:4px">Armazém<br>Geral</div>
          <div style="display:flex;gap:2px;margin-top:5px">
            <div :style="{ padding:'2px 5px', borderRadius:'6px', background:'#fff', color:primary, fontSize:'3.8px', fontWeight:'800' }">Em alta</div>
            <div style="padding:2px 5px;border-radius:6px;border:0.8px solid rgba(255,255,255,0.7);color:#fff;font-size:3.8px;font-weight:800">Catálogo</div>
          </div>
        </div>
        <div style="position:absolute;right:9px;top:12%;width:30%;height:76%;border-radius:6px;border:2.5px solid #fff;background:rgba(255,255,255,0.35);transform:rotate(-5deg);box-shadow:0 6px 12px rgba(0,0,0,0.2)"></div>
      </div>
      <div style="position:absolute;top:70%;left:-4px;right:-4px;padding:2px 0;background:#17130f;transform:rotate(-1.5deg);display:flex;gap:6px;justify-content:center;white-space:nowrap">
        <span v-for="t in ['Armazém','Moda','Entrega grátis']" :key="t" style="display:inline-flex;align-items:center;gap:6px;color:#fff8ef;font-size:4.5px;font-weight:800">
          {{ t }}<span :style="{ width:'3px', height:'3px', borderRadius:'50%', background:primary, display:'inline-block' }"></span>
        </span>
      </div>
      <div style="position:absolute;bottom:6px;left:7px;right:7px;display:grid;grid-template-columns:repeat(4,1fr);gap:3px">
        <div v-for="(o, i) in [0.18, 0.32, 0.1, 0.45]" :key="i"
             :style="{ height:'20px', borderRadius:'6px', padding:'2px', background:'color-mix(in srgb,' + primary + ' ' + (o * 100) + '%, #fff)' }">
          <div style="height:100%;border-radius:4px;background:rgba(255,255,255,0.55)"></div>
        </div>
      </div>
    </template>

    <!-- ── NATUREZA ── -->
    <template v-else-if="id === 'natureza'">
      <div style="position:absolute;inset:0;background:#f5f1e6"></div>
      <div style="position:absolute;top:5px;left:6px;display:flex;gap:2px">
        <div style="width:7px;height:7px;border-radius:50%;background:#fffdf7;border:0.5px solid rgba(35,41,31,0.2)"></div>
        <div style="width:7px;height:7px;border-radius:50%;background:#fffdf7;border:0.5px solid rgba(35,41,31,0.2)"></div>
      </div>
      <div style="position:absolute;top:20%;left:7px;width:48%">
        <div :style="{ fontSize:'3.5px', fontWeight:'600', letterSpacing:'0.06em', color:primary }">PRODUTOS NATURAIS</div>
        <div style="font-size:13px;line-height:1;color:#23291f;margin:3px 0 4px;font-family:Georgia,serif">Armazém Geral</div>
        <div v-for="t in ['4.8 · 124 avaliações','Entrega grátis','Lisboa']" :key="t" style="display:flex;align-items:center;gap:2px;margin-top:1.5px">
          <span :style="{ width:'3px', height:'3px', borderRadius:'50%', background:primary, display:'inline-block' }"></span>
          <span style="font-size:3.5px;color:#23291f">{{ t }}</span>
        </div>
        <div :style="{ display:'inline-block', marginTop:'4px', padding:'2px 6px', borderRadius:'6px', background:primary, color:'#fff', fontSize:'3.6px', fontWeight:'600' }">Da época</div>
      </div>
      <div :style="{ position:'absolute', top:'14%', right:'8px', width:'38%', aspectRatio:'1', background:'linear-gradient(150deg,#a8c48a,'+primary+')', borderRadius:'58% 42% 52% 48% / 46% 54% 46% 54%' }"></div>
      <div style="position:absolute;top:44%;right:36%;width:16px;height:16px;border-radius:50%;background:#fffdf7;border:0.5px solid rgba(35,41,31,0.2)"></div>
      <div style="position:absolute;bottom:5px;left:7px;right:7px;display:grid;grid-template-columns:1.1fr 1fr 1fr 1fr;gap:3px">
        <div :style="{ height:'24px', borderRadius:'5px', padding:'3px', background:'color-mix(in srgb,'+primary+' 16%, #f5f1e6)' }">
          <div style="font-size:4px;color:#23291f;font-family:Georgia,serif">Frutas</div>
          <div style="font-size:2.8px;color:#66705c">12 produtos</div>
        </div>
        <div v-for="i in 3" :key="i" style="display:flex;flex-direction:column;gap:1px">
          <div :style="{ height:'17px', borderRadius:'5px', background:'color-mix(in srgb,'+primary+' '+(18 + i * 8)+'%, #f5f1e6)' }"></div>
          <div style="height:5px;border-radius:1px 1px 3px 3px;background:#e3cfa8;border-top:0.5px dashed rgba(74,58,30,0.4)"></div>
        </div>
      </div>
    </template>

    <!-- ── LUXO PREMIUM ── -->
    <template v-else-if="id === 'luxo_premium'">
      <div style="position:absolute;inset:0;background:radial-gradient(ellipse at 50% 40%,#3a3127,#0e0d0c 70%)"></div>
      <div :style="{ position:'absolute', top:'16px', left:'6px', right:'6px', bottom:'34%', border:'0.5px solid ' + primary, opacity:'0.6' }"></div>
      <div style="position:absolute;top:5px;left:6px;display:flex;gap:2px">
        <div style="width:7px;height:7px;border-radius:50%;border:0.5px solid rgba(241,236,227,0.7)"></div>
        <div style="width:7px;height:7px;border-radius:50%;border:0.5px solid rgba(241,236,227,0.7)"></div>
      </div>
      <div style="position:absolute;top:22%;left:0;right:0;display:flex;flex-direction:column;align-items:center">
        <div :style="{ width:'11px', height:'11px', borderRadius:'50%', border:'0.5px solid '+primary, color:primary, fontSize:'6px', fontStyle:'italic', fontFamily:'Georgia,serif', display:'flex', alignItems:'center', justifyContent:'center' }">A</div>
        <div :style="{ fontSize:'3px', letterSpacing:'0.36em', color:primary, marginTop:'3px' }">MAISON — LISBOA</div>
        <div style="font-size:13px;color:#f1ece3;font-family:Georgia,serif;letter-spacing:0.02em;margin:2px 0 4px">Armazém</div>
        <div :style="{ padding:'2px 6px', background:primary, color:'#0e0d0c', fontSize:'3px', letterSpacing:'0.3em' }">DESCOBRIR</div>
      </div>
      <div style="position:absolute;bottom:6px;left:7px;right:7px;height:26%;display:grid;grid-template-columns:1.1fr 0.9fr;gap:5px;align-items:center">
        <div style="height:100%;border:0.5px solid rgba(241,236,227,0.12);background:radial-gradient(ellipse at 50% 40%,rgba(184,151,90,0.28),transparent 65%),#1a1816;display:flex;align-items:center;justify-content:center">
          <div style="width:30%;height:60%;border-radius:2px;background:linear-gradient(160deg,#c9b48a,#6f5a37)"></div>
        </div>
        <div>
          <div :style="{ fontSize:'2.8px', letterSpacing:'0.3em', color:primary }">Nº 01</div>
          <div style="font-size:6px;color:#f1ece3;font-family:Georgia,serif;margin:1px 0">Colar Aurora</div>
          <div :style="{ fontSize:'5px', fontStyle:'italic', color:primary, fontFamily:'Georgia,serif' }">1 250,00 €</div>
        </div>
      </div>
    </template>

    <!-- ── DESPORTO ── -->
    <template v-else-if="id === 'desporto'">
      <div style="position:absolute;inset:0;background:#101114"></div>
      <div style="position:absolute;top:0;bottom:0;right:-8%;width:60%;display:flex;gap:5px;transform:skewX(-18deg)">
        <div :style="{ flex:'1', background:primary, opacity:'0.1' }"></div>
        <div :style="{ flex:'0.5', background:primary, opacity:'0.18' }"></div>
        <div :style="{ flex:'0.3', background:primary, opacity:'0.06' }"></div>
      </div>
      <div style="position:absolute;top:5px;left:6px;display:flex;gap:2px">
        <div style="width:7px;height:7px;border-radius:1.5px;background:#1d1f24;border:0.5px solid rgba(244,245,247,0.15)"></div>
        <div style="width:7px;height:7px;border-radius:1.5px;background:#1d1f24;border:0.5px solid rgba(244,245,247,0.15)"></div>
      </div>
      <div style="position:absolute;top:21%;left:7px;width:52%">
        <div :style="{ display:'inline-block', padding:'1px 4px', background:primary, color:'#0c0d0f', fontSize:'3.5px', fontWeight:'800', transform:'skewX(-12deg)' }">DESPORTO</div>
        <div style="font-size:15px;font-weight:900;font-style:italic;text-transform:uppercase;line-height:0.88;color:#f4f5f7;letter-spacing:-0.03em;margin:3px 0 4px">ARMAZÉM<br>GERAL</div>
        <div :style="{ display:'inline-block', padding:'2px 6px', borderRadius:'1.5px', background:primary, color:'#0c0d0f', fontSize:'3.8px', fontWeight:'800' }">VER O TOP →</div>
      </div>
      <div style="position:absolute;top:20%;right:7px;width:38%;height:34%;background:linear-gradient(150deg,#3a3f48,#20232a);clip-path:polygon(14% 0,100% 0,86% 100%,0 100%)"></div>
      <div style="position:absolute;top:62%;left:7px;right:7px;display:grid;grid-template-columns:repeat(4,1fr);background:#1d1f24;border:0.5px solid rgba(244,245,247,0.1);border-radius:2px">
        <div v-for="([l, v], i) in [['AVAL.','4.8'],['PROD.','124'],['MODAL.','6'],['ENTR.','Grátis']]" :key="l"
             :style="{ padding:'2px 3px', borderLeft: i ? '0.5px solid rgba(244,245,247,0.1)' : 'none' }">
          <div style="font-size:2.5px;color:#9aa0aa;font-weight:700">{{ l }}</div>
          <div :style="{ fontSize:'6px', fontWeight:'900', fontStyle:'italic', color: i < 3 ? primary : '#f4f5f7' }">{{ v }}</div>
        </div>
      </div>
      <div style="position:absolute;bottom:5px;left:7px;right:7px;display:flex;gap:3px">
        <div v-for="i in 4" :key="i" style="position:relative;flex:1;height:18px;border-radius:2px;background:#1d1f24;border:0.5px solid rgba(244,245,247,0.1)">
          <span :style="{ position:'absolute', top:'-3px', left:'2px', fontSize:'7px', fontWeight:'900', fontStyle:'italic', color:'transparent', WebkitTextStroke:'0.5px ' + primary }">0{{ i }}</span>
        </div>
      </div>
    </template>

    <!-- ── FALLBACK ── -->
    <template v-else>
      <div style="position:absolute;inset:0;display:flex;align-items:center;justify-content:center;flex-direction:column;gap:4px">
        <div :style="{ width:'28px', height:'28px', borderRadius:'50%', background:primary, display:'flex', alignItems:'center', justifyContent:'center', fontSize:'14px', fontWeight:'900', color:'#fff' }">{{(template.nome||'T').charAt(0)}}</div>
        <span style="font-size:9px;font-weight:700;color:#fafafa">{{template.nome}}</span>
      </div>
    </template>

  </div>
</template>

<script>
const BG_MAP = {
  'classico':            '#09090b',
  'minimalista':         '#f4f2ee',
  'moda_boutique':       '#faf5f2',
  'moda_editorial':      '#09090b',
  'restaurante_bistro':  '#f6efe2',
  'restaurante_moderno': '#14110f',
  'tech_store':          '#0b0f17',
  'vibrante':            '#fff8ef',
  'natureza':            '#f5f1e6',
  'luxo_premium':        '#0e0d0c',
  'desporto':            '#101114',
}

export default {
  name: 'TemplateMiniPreview',
  props: {
    template: { type: Object, required: true },
  },
  computed: {
    id ()      { return this.template.id },
    primary () { return this.template.primaryDefault || this.template.primary || '#dc2626' },
    rootStyle () {
      return {
        position:   'relative',
        width:      '100%',
        height:     '100%',
        overflow:   'hidden',
        fontFamily: "'DM Sans', sans-serif",
        color:      '#fff',
        background: BG_MAP[this.id] || '#111113',
      }
    },
  },
  methods: {
    abs (extra = {}) {
      return { position: 'absolute', inset: '0', ...extra }
    },
  },
}
</script>

<style scoped>
@keyframes marquee-mini {
  0%   { transform: translateX(0); }
  100% { transform: translateX(-50%); }
}
</style>