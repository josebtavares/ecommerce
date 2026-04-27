<!-- TemplateMiniPreview.vue
     Renderiza um preview visual CSS para cada template.
     Uso: <TemplateMiniPreview :template="tpl" />
-->
<template>
  <div class="mini-root" :style="{ background: bg }">

    <!-- ── CLÁSSICO ── -->
    <template v-if="id === 'classico'">
      <div class="abs inset stripe" style="background:rgba(9,9,11,0.55)"></div>
      <div class="abs" style="inset:0;background:linear-gradient(to top,#09090b 0%,transparent 55%)"></div>
      <div class="abs" style="top:7px;left:7px;width:18px;height:18px;border-radius:50%;background:rgba(0,0,0,0.5);display:flex;align-items:center;justify-content:center">
        <span style="color:#fff;font-size:8px">←</span>
      </div>
      <div class="abs" style="bottom:42%;left:8px;display:flex;align-items:flex-end;gap:5px">
        <div :style="{ width:'24px',height:'24px',borderRadius:'5px',background:primary,display:'flex',alignItems:'center',justifyContent:'center',fontSize:'11px',fontWeight:'900',color:'#fff',flexShrink:0 }">A</div>
        <div>
          <div :style="{ fontSize:'4px',color:primary,fontWeight:'700',letterSpacing:'0.1em',textTransform:'uppercase' }">Moda</div>
          <div style="font-size:9px;font-weight:800;color:#fff;line-height:1.1">Armazém Geral</div>
          <div style="font-size:4px;color:#a1a1aa;margin-top:1px">📍 Lisboa · ⭐ 4.8</div>
        </div>
      </div>
      <div class="abs" style="bottom:20%;left:8px;right:8px;display:grid;grid-template-columns:2fr 1fr;gap:3px">
        <div style="background:#18181b;border:1px solid #27272a;border-radius:4px;padding:3px 5px">
          <div style="font-size:3px;color:#52525b;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:1px">Sobre</div>
          <div style="font-size:4px;color:#71717a;line-height:1.3">Curadoria de peças únicas para quem valoriza o detalhe.</div>
        </div>
        <div style="background:#18181b;border:1px solid #27272a;border-radius:4px;padding:3px 5px">
          <div style="font-size:3px;color:#52525b;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:1px">Entrega</div>
          <div style="font-size:5px;color:#4ade80;font-weight:600">✓ Grátis</div>
        </div>
      </div>
      <div class="abs" style="bottom:4%;left:8px;right:8px">
        <div style="font-size:5px;font-weight:700;color:#71717a;margin-bottom:2px">Em Destaque</div>
        <div style="display:flex;gap:3px">
          <div v-for="i in 4" :key="i" style="flex-shrink:0;width:42px;background:#18181b;border:1px solid #27272a;border-radius:4px;overflow:hidden">
            <div style="height:22px;position:relative;overflow:hidden"><div class="abs stripe" style="background:rgba(0,0,0,0.4)"></div></div>
            <div style="padding:2px 3px">
              <div style="font-size:3.5px;color:#e4e4e7;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">Produto</div>
              <div :style="{ fontSize:'3.5px',color:primary,fontWeight:'700' }">89,90€</div>
            </div>
          </div>
        </div>
      </div>
    </template>

    <!-- ── MINIMALISTA ── -->
    <template v-else-if="id === 'minimalista'">
      <div class="abs inset stripe" style="opacity:0.07;background:rgba(0,0,0,0)"></div>
      <div class="abs" style="left:5px;top:20%;bottom:20%;width:0.5px;background:#292524"></div>
      <div class="abs" style="top:8px;left:10px;font-size:5px;letter-spacing:0.3em;text-transform:uppercase;color:#57534e">← Voltar</div>
      <div class="abs" style="bottom:30%;left:12px;right:8px">
        <div style="font-size:5.5px;letter-spacing:0.4em;text-transform:uppercase;color:#57534e;margin-bottom:5px">Moda · Lisboa</div>
        <div style="font-size:26px;font-weight:900;line-height:0.88;letter-spacing:-0.04em;color:#fafaf9;word-break:break-all">Armazém</div>
      </div>
      <div class="abs" style="bottom:14%;left:12px;display:flex;gap:14px">
        <div v-for="([v,c,l]) in [['4.8',primary,'Rating'],['124','#fafaf9','Reviews']]" :key="l">
          <div :style="{ fontSize:'13px',fontWeight:'900',color:c,lineHeight:'1' }">{{v}}</div>
          <div style="font-size:3.5px;letter-spacing:0.3em;text-transform:uppercase;color:#57534e;margin-top:1px">{{l}}</div>
        </div>
      </div>
      <div class="abs" style="bottom:5%;left:12px;display:flex;align-items:center;gap:5px">
        <div :style="{ width:'14px',height:'0.5px',background:primary }"></div>
        <div style="font-size:4.5px;letter-spacing:0.2em;text-transform:uppercase;color:#78716c">Ver coleção</div>
      </div>
    </template>

    <!-- ── MODA BOUTIQUE ── -->
    <template v-else-if="id === 'moda-boutique'">
      <div style="position:absolute;inset:0;display:flex">
        <div style="width:52%;position:relative;overflow:hidden">
          <div class="abs stripe" style="background:rgba(10,8,5,0.45)"></div>
          <div class="abs" style="background:linear-gradient(to right,transparent 60%,#0a0805)"></div>
        </div>
        <div style="width:48%;display:flex;flex-direction:column;justify-content:center;padding:10px 8px 10px 4px;background:#0a0805">
          <div :style="{ fontSize:'4px',letterSpacing:'0.3em',textTransform:'uppercase',color:primary,marginBottom:'4px',fontFamily:'DM Sans,sans-serif' }">Sobre</div>
          <div style="font-size:12px;font-style:italic;font-weight:400;color:#fef3c7;line-height:1.1;font-family:Georgia,serif;margin-bottom:5px">Armazém Geral</div>
          <div style="font-size:4px;color:#78350f;line-height:1.4;font-family:DM Sans,sans-serif;margin-bottom:6px">Curadoria de peças únicas.</div>
          <div :style="{ display:'inline-flex',padding:'3px 7px',background:primary,color:'#fff',fontSize:'4px',fontFamily:'DM Sans,sans-serif',fontWeight:'600',letterSpacing:'0.1em',textTransform:'uppercase',alignSelf:'flex-start' }">Ver Coleção</div>
          <div style="margin-top:7px">
            <div :style="{ fontSize:'11px',fontStyle:'italic',color:primary,fontFamily:'Georgia,serif',lineHeight:'1' }">4.8</div>
            <div style="font-size:3.5px;letter-spacing:0.2em;text-transform:uppercase;color:#78350f;font-family:DM Sans,sans-serif">Rating</div>
          </div>
        </div>
      </div>
      <div class="abs" style="top:7px;left:7px;width:16px;height:16px;border-radius:50%;background:rgba(255,255,255,0.12);display:flex;align-items:center;justify-content:center">
        <span style="color:#fff;font-size:7px">←</span>
      </div>
    </template>

    <!-- ── MODA EDITORIAL ── -->
    <template v-else-if="id === 'moda-editorial'">
      <div style="position:absolute;inset:0;display:grid;grid-template-columns:3fr 2fr">
        <div style="position:relative;overflow:hidden">
          <div class="abs stripe" style="background:rgba(9,9,11,0.25)"></div>
          <div style="position:absolute;bottom:-4px;left:6px;font-size:34px;font-weight:900;color:rgba(255,255,255,0.05);line-height:1;letter-spacing:-0.05em;user-select:none">2025</div>
          <div class="abs" style="background:linear-gradient(to right,transparent 55%,#09090b)"></div>
        </div>
        <div style="display:flex;flex-direction:column;justify-content:center;padding:12px 8px 12px 4px">
          <div :style="{ fontSize:'4px',letterSpacing:'0.5em',textTransform:'uppercase',color:primary,marginBottom:'5px' }">Moda</div>
          <div style="font-size:14px;font-weight:900;letter-spacing:-0.04em;line-height:0.9;color:#fafafa;margin-bottom:5px;word-break:break-word">Armazém Geral</div>
          <div style="display:flex;align-items:center;gap:3px;margin-bottom:5px">
            <div style="flex:1;height:0.5px;background:#27272a"></div>
            <div :style="{ width:'5px',height:'5px',transform:'rotate(45deg)',background:primary,flexShrink:'0' }"></div>
            <div style="flex:1;height:0.5px;background:#27272a"></div>
          </div>
          <div style="font-size:4px;color:#52525b;margin-bottom:5px;line-height:1.4">Curadoria exclusiva de peças.</div>
          <div :style="{ display:'inline-flex',padding:'3px 7px',background:primary,color:'#09090b',fontSize:'4px',fontWeight:'900',textTransform:'uppercase',alignSelf:'flex-start' }">Ver Coleção</div>
        </div>
      </div>
    </template>

    <!-- ── RESTAURANTE BISTRO ── -->
    <template v-else-if="id === 'restaurante-bistro'">
      <div style="position:absolute;top:0;left:0;right:0;height:44%">
        <div class="abs stripe light" style="background:rgba(26,20,16,0.3)"></div>
        <div class="abs" style="background:linear-gradient(to bottom,transparent 40%,#fdf6ec)"></div>
        <div :style="{ position:'absolute',top:'5px',left:'5px',width:'9px',height:'9px',borderTop:'1px solid '+primary,borderLeft:'1px solid '+primary }"></div>
        <div :style="{ position:'absolute',bottom:'12px',right:'5px',width:'9px',height:'9px',borderBottom:'1px solid '+primary,borderRight:'1px solid '+primary }"></div>
      </div>
      <div class="abs" style="top:36%;left:0;right:0;bottom:0;display:flex;flex-direction:column;align-items:center;padding:3px 10px 5px">
        <div style="display:flex;align-items:center;gap:3px;width:100%;margin-bottom:3px">
          <div style="flex:1;height:0.5px;background:rgba(217,119,6,0.3)"></div>
          <span :style="{ fontSize:'6px',color:primary }">✦</span>
          <div style="flex:1;height:0.5px;background:rgba(217,119,6,0.3)"></div>
        </div>
        <div style="font-size:4px;letter-spacing:0.3em;text-transform:uppercase;color:#92400e;margin-bottom:2px">Restauração · Lisboa</div>
        <div style="font-size:16px;font-style:italic;font-weight:400;color:#1c1410;line-height:1.1;text-align:center;font-family:Georgia,serif">Armazém Geral</div>
        <div style="display:grid;grid-template-columns:1fr auto 1fr;gap:3px;margin-top:4px;width:100%;border-top:0.5px solid rgba(217,119,6,0.2);border-bottom:0.5px solid rgba(217,119,6,0.2);padding:3px 0;align-items:center">
          <div style="text-align:center"><div :style="{ fontSize:'10px',fontStyle:'italic',color:primary,fontFamily:'Georgia,serif' }">4.8</div><div style="font-size:3px;letter-spacing:0.2em;text-transform:uppercase;color:rgba(146,64,14,0.5)">Aval.</div></div>
          <div style="width:0.5px;height:18px;background:rgba(217,119,6,0.2)"></div>
          <div style="text-align:center"><div :style="{ fontSize:'10px',fontStyle:'italic',color:primary,fontFamily:'Georgia,serif' }">0€</div><div style="font-size:3px;letter-spacing:0.2em;text-transform:uppercase;color:rgba(146,64,14,0.5)">Entrega</div></div>
        </div>
        <div style="margin-top:4px">
          <div :style="{ padding:'3px 9px',background:primary,color:'#fff',fontSize:'5px',fontStyle:'italic',fontFamily:'Georgia,serif' }">Ver o Menu →</div>
        </div>
      </div>
    </template>

    <!-- ── RESTAURANTE MODERNO ── -->
    <template v-else-if="id === 'restaurante-moderno'">
      <div class="abs stripe" style="background:rgba(9,9,11,0.65)"></div>
      <div class="abs" style="background:radial-gradient(ellipse at center,transparent 30%,rgba(9,9,11,0.7) 100%)"></div>
      <div class="abs" style="bottom:0;left:0;right:0;height:65%;background:linear-gradient(to top,#09090b,transparent)"></div>
      <div class="abs" style="top:8px;left:9px;display:flex;align-items:center;gap:4px">
        <div style="width:12px;height:0.5px;background:rgba(255,255,255,0.4)"></div>
        <span style="font-size:4px;letter-spacing:0.25em;text-transform:uppercase;color:rgba(255,255,255,0.4)">Voltar</span>
      </div>
      <div class="abs" style="bottom:10px;left:9px">
        <div style="display:flex;align-items:center;gap:4px;margin-bottom:3px">
          <div :style="{ width:'10px',height:'0.5px',background:primary }"></div>
          <span style="font-size:3.5px;letter-spacing:0.3em;text-transform:uppercase;color:rgba(255,255,255,0.4)">Restauração</span>
        </div>
        <div style="font-size:19px;font-weight:900;letter-spacing:-0.03em;line-height:0.9;color:#fff">Armazém Geral</div>
        <div style="font-size:4px;color:rgba(255,255,255,0.45);margin-top:3px;margin-bottom:4px">Curadoria de sabores únicos</div>
        <div style="display:flex;gap:3px">
          <div :style="{ padding:'3px 7px',background:primary,color:'#fff',fontSize:'4px',fontWeight:'700',textTransform:'uppercase' }">Ver Menu</div>
          <div style="padding:3px 7px;border:1px solid rgba(255,255,255,0.25);color:rgba(255,255,255,0.6);font-size:4px;font-weight:700">★ Reviews</div>
        </div>
      </div>
      <div class="abs" style="bottom:24px;right:9px;text-align:right">
        <div style="font-size:16px;font-weight:900;color:#fff;line-height:1">4.8</div>
        <div style="font-size:3.5px;letter-spacing:0.2em;text-transform:uppercase;color:rgba(255,255,255,0.25)">/ 5 stars</div>
      </div>
    </template>

    <!-- ── TECH STORE ── -->
    <template v-else-if="id === 'tech-store'">
      <div class="abs" style="opacity:0.07;background-image:linear-gradient(to right,#06b6d4 1px,transparent 1px),linear-gradient(to bottom,#06b6d4 1px,transparent 1px);background-size:18px 18px"></div>
      <div class="abs" style="top:-20px;right:-20px;width:110px;height:110px;border-radius:50%;background:radial-gradient(circle,rgba(6,182,212,0.3),transparent);pointer-events:none"></div>
      <div class="abs stripe" style="opacity:0.1;background:rgba(0,0,0,0)"></div>
      <div class="abs" style="top:7px;left:7px;padding:2px 5px;border:1px solid #1e293b;border-radius:3px;font-size:4px;color:#64748b;font-family:Space Mono,monospace">← BACK</div>
      <div class="abs" style="top:20%;left:0;right:0;text-align:center">
        <div :style="{ display:'inline-flex',alignItems:'center',gap:'3px',padding:'2px 7px',border:'1px solid '+primary+'30',borderRadius:'10px',marginBottom:'7px' }">
          <div :style="{ width:'4px',height:'4px',borderRadius:'50%',background:primary }"></div>
          <span :style="{ fontSize:'4px',color:primary,letterSpacing:'0.3em',textTransform:'uppercase',fontFamily:'Space Mono,monospace' }">Tech</span>
        </div>
        <div style="font-size:15px;font-weight:900;letter-spacing:-0.04em;line-height:1;background:linear-gradient(135deg,#e2e8f0,#94a3b8,#67e8f9);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text">Armazém</div>
      </div>
      <div class="abs" style="bottom:18%;left:7px;right:7px;display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:3px">
        <div v-for="([v,c,l]) in [['4.8',primary,'Rating'],['124','#e2e8f0','Reviews'],['ON','#4ade80','Entrega'],['8','#94a3b8','Cats']]" :key="l"
             style="background:rgba(15,23,42,0.8);border:1px solid rgba(30,41,59,0.7);border-radius:4px;padding:3px 2px;text-align:center">
          <div :style="{ fontSize:'9px',fontWeight:'700',color:c,lineHeight:'1',fontFamily:'Space Mono,monospace' }">{{v}}</div>
          <div style="font-size:3px;letter-spacing:0.1em;text-transform:uppercase;color:#334155;margin-top:1px;font-family:Space Mono,monospace">{{l}}</div>
        </div>
      </div>
      <div class="abs" style="bottom:5%;left:50%;transform:translateX(-50%)">
        <div :style="{ padding:'3px 10px',borderRadius:'4px',fontSize:'4px',fontWeight:'700',color:'#fff',background:'linear-gradient(135deg,'+primary+',#1d4ed8)',whiteSpace:'nowrap',fontFamily:'Space Mono,monospace' }">Explorar ↓</div>
      </div>
    </template>

    <!-- ── VIBRANTE ── -->
    <template v-else-if="id === 'vibrante'">
      <div class="abs stripe" style="opacity:0.2;background:rgba(0,0,0,0)"></div>
      <div :style="{ position:'absolute',top:'0',right:'0',width:'44%',height:'100%',background:primary,opacity:'0.88' }"></div>
      <div class="abs" style="bottom:0;left:0;width:65%;height:38%;background:#18181b;transform:skewY(-4deg);transform-origin:left bottom"></div>
      <div class="abs" style="top:10px;left:9px;display:inline-flex;align-items:center;gap:3px;padding:2px 6px;border-radius:10px" :style="{ background:primary }">
        <div style="width:4px;height:4px;border-radius:50%;background:#fff"></div>
        <span style="font-size:4px;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;color:#fff">Streetwear</span>
      </div>
      <div class="abs" style="top:26%;left:9px">
        <div style="font-size:21px;font-weight:900;text-transform:uppercase;line-height:0.88;letter-spacing:-0.02em;color:#fff">ARMAZÉM</div>
        <div style="font-size:19px;font-weight:900;text-transform:uppercase;line-height:0.9;letter-spacing:-0.02em;color:transparent;-webkit-text-stroke:1.5px #fff">GERAL</div>
      </div>
      <div class="abs" style="bottom:26%;left:9px;display:flex;gap:3px">
        <div :style="{ padding:'3px 7px',borderRadius:'4px',background:primary,color:'#fff',fontSize:'4.5px',fontWeight:'900',textTransform:'uppercase' }">Coleção</div>
        <div style="padding:3px 7px;border-radius:4px;border:1.5px solid #fff;color:#fff;font-size:4.5px;font-weight:900;text-transform:uppercase">Catálogo</div>
      </div>
      <div class="abs" style="bottom:8px;left:0;right:0;overflow:hidden;padding:3px 0" :style="{ background:primary }">
        <div class="marquee-strip" style="display:flex;gap:8px;white-space:nowrap">
          <span v-for="i in 6" :key="i" style="color:#fff;font-size:4.5px;font-weight:900;text-transform:uppercase;letter-spacing:0.1em;display:inline-flex;align-items:center;gap:6px;flex-shrink:0">
            New Drop <span style="width:3px;height:3px;border-radius:50%;background:#fff;display:inline-block"></span> Limited Edition <span style="width:3px;height:3px;border-radius:50%;background:#fff;display:inline-block"></span>
          </span>
        </div>
      </div>
    </template>

    <!-- ── NATUREZA ── -->
    <template v-else-if="id === 'natureza'">
      <div class="abs" style="inset:0;background:linear-gradient(135deg,#051a0a 0%,#0a2e12 50%,#051a0a 100%)"></div>
      <div class="abs" style="opacity:0.06;background-image:radial-gradient(circle,#4ade80 1px,transparent 1px);background-size:12px 12px"></div>
      <div class="abs" style="top:0;right:0;width:55%;height:100%;overflow:hidden">
        <div class="abs stripe" style="background:rgba(5,26,10,0.4)"></div>
        <div class="abs" style="background:linear-gradient(to left,transparent 30%,#051a0a)"></div>
      </div>
      <div class="abs" style="top:8px;left:9px;font-size:5px;letter-spacing:0.25em;text-transform:uppercase;color:rgba(74,222,128,0.4)">← Voltar</div>
      <div class="abs" style="bottom:35%;left:12px">
        <div style="font-size:5px;letter-spacing:0.4em;text-transform:uppercase;color:rgba(74,222,128,0.5);margin-bottom:5px">Bio · Natural · Lisboa</div>
        <div :style="{ fontSize:'20px',fontWeight:'900',lineHeight:'0.9',letterSpacing:'-0.03em',color:'#f0fdf4' }">Armazém<br>Geral</div>
        <div style="font-size:4.5px;color:rgba(187,247,208,0.5);margin-top:5px;line-height:1.4;max-width:100px">Produtos naturais e orgânicos com impacto positivo.</div>
      </div>
      <div class="abs" style="bottom:12%;left:12px;display:flex;gap:5px">
        <div :style="{ padding:'3px 8px',borderRadius:'12px',background:primary,color:'#fff',fontSize:'4.5px',fontWeight:'700' }">Ver Produtos</div>
        <div style="padding:3px 8px;border-radius:12px;border:1px solid rgba(74,222,128,0.3);color:rgba(187,247,208,0.7);font-size:4.5px;font-weight:600">Sobre nós</div>
      </div>
      <div class="abs" style="bottom:4%;left:12px;display:flex;gap:12px">
        <div v-for="([v,l]) in [['4.8','Rating'],['100%','Bio'],['✓','Entrega']]" :key="l">
          <div :style="{ fontSize:'11px',fontWeight:'900',color:primary,lineHeight:'1' }">{{v}}</div>
          <div style="font-size:3.5px;letter-spacing:0.2em;text-transform:uppercase;color:rgba(74,222,128,0.4);margin-top:1px">{{l}}</div>
        </div>
      </div>
    </template>

    <!-- ── LUXO PREMIUM ── -->
    <template v-else-if="id === 'luxo-premium'">
      <div class="abs" style="inset:0;background:#030303"></div>
      <div class="abs stripe" style="opacity:0.04;background:rgba(0,0,0,0)"></div>
      <div :style="{ position:'absolute',top:'-30px',left:'50%',transform:'translateX(-50%)',width:'160px',height:'160px',borderRadius:'50%',background:'radial-gradient(circle,rgba(201,168,76,0.12),transparent)',pointerEvents:'none' }"></div>
      <div class="abs" style="top:8px;left:50%;transform:translateX(-50%);white-space:nowrap;font-size:4px;letter-spacing:0.5em;text-transform:uppercase;color:rgba(201,168,76,0.35);font-family:Georgia,serif">MAISON ARMAZÉM</div>
      <div class="abs" style="top:0;bottom:0;left:0;right:0;display:flex;flex-direction:column;justify-content:center;align-items:center;text-align:center;padding:12px">
        <div :style="{ width:'20px',height:'0.5px',background:primary,margin:'0 auto 8px' }"></div>
        <div :style="{ fontSize:'18px',fontStyle:'italic',fontWeight:'400',color:'#fef3c7',lineHeight:'1.1',fontFamily:'Georgia,serif',letterSpacing:'0.02em' }">Armazém<br>Geral</div>
        <div :style="{ width:'20px',height:'0.5px',background:primary,margin:'8px auto' }"></div>
        <div style="font-size:4px;letter-spacing:0.3em;text-transform:uppercase;color:rgba(201,168,76,0.5);font-family:DM Sans,sans-serif;margin-bottom:8px">Collection · 2025</div>
        <div :style="{ padding:'4px 12px',border:'0.5px solid '+primary+'80',color:primary,fontSize:'4px',letterSpacing:'0.25em',textTransform:'uppercase',fontFamily:'DM Sans,sans-serif' }">Découvrir</div>
      </div>
      <div class="abs" style="bottom:6px;left:0;right:0;display:flex;justify-content:center;gap:10px">
        <div v-for="([v,l]) in [['4.9','Rating'],['Lisboa','Local'],['✦','Exclusivo']]" :key="l" style="text-align:center">
          <div :style="{ fontSize:'8px',fontStyle:'italic',color:primary,fontFamily:'Georgia,serif',lineHeight:'1' }">{{v}}</div>
          <div style="font-size:3px;letter-spacing:0.3em;text-transform:uppercase;color:rgba(201,168,76,0.3);margin-top:1px">{{l}}</div>
        </div>
      </div>
    </template>

    <!-- ── DESPORTO ── -->
    <template v-else-if="id === 'desporto'">
      <div class="abs" style="inset:0;background:#0a0a0a"></div>
      <div class="abs stripe" style="opacity:0.15;background:rgba(0,0,0,0)"></div>
      <div :style="{ position:'absolute',top:0,right:0,width:'50%',height:'100%',background:primary,clipPath:'polygon(20% 0,100% 0,100% 100%,0% 100%)' }"></div>
      <div class="abs" style="bottom:0;left:0;width:70%;height:30%;background:#111;transform:skewY(-6deg);transform-origin:left bottom"></div>
      <div class="abs" style="top:8px;left:9px;font-size:4.5px;letter-spacing:0.1em;text-transform:uppercase;color:rgba(255,255,255,0.4)">← Voltar</div>
      <div :style="{ position:'absolute',top:'18%',left:'9px',right:'52%' }">
        <div :style="{ display:'inline-flex',alignItems:'center',gap:'3px',padding:'2px 6px',background:primary,borderRadius:'2px',marginBottom:'8px' }">
          <span style="font-size:4px;font-weight:900;color:#fff;text-transform:uppercase;letter-spacing:0.1em">Desporto</span>
        </div>
        <div style="font-size:22px;font-weight:900;text-transform:uppercase;line-height:0.85;color:#fff;letter-spacing:-0.03em">ARMAZÉM<br>GERAL</div>
        <div style="font-size:4px;color:rgba(255,255,255,0.45);margin-top:5px;line-height:1.4">Equipamento de alta performance.</div>
        <div style="display:flex;gap:3px;margin-top:6px">
          <div :style="{ padding:'3px 8px',background:primary,color:'#fff',fontSize:'4.5px',fontWeight:'900',textTransform:'uppercase',borderRadius:'2px' }">Shop Now</div>
          <div style="padding:3px 8px;border:1.5px solid rgba(255,255,255,0.4);color:rgba(255,255,255,0.7);font-size:4.5px;font-weight:900;text-transform:uppercase;border-radius:2px">Catálogo</div>
        </div>
      </div>
      <div class="abs" style="bottom:5%;left:9px;display:flex;gap:10px">
        <div v-for="([v,l]) in [['4.9','Rating'],['✓','Stock'],['2h','Entrega']]" :key="l">
          <div :style="{ fontSize:'11px',fontWeight:'900',color:primary,lineHeight:'1' }">{{v}}</div>
          <div style="font-size:3.5px;letter-spacing:0.2em;text-transform:uppercase;color:rgba(255,255,255,0.3);margin-top:1px">{{l}}</div>
        </div>
      </div>
    </template>

    <!-- ── FALLBACK ── -->
    <template v-else>
      <div class="abs" style="display:flex;align-items:center;justify-content:center;flex-direction:column;gap:4px">
        <div :style="{ width:'28px',height:'28px',borderRadius:'50%',background:primary,display:'flex',alignItems:'center',justifyContent:'center',fontSize:'14px',fontWeight:'900',color:'#fff' }">{{(template.nome||'T').charAt(0)}}</div>
        <span style="font-size:9px;font-weight:700;color:#fafafa">{{template.nome}}</span>
      </div>
    </template>

  </div>
</template>

<script>
export default {
  name: 'TemplateMiniPreview',
  props: {
    template: { type: Object, required: true },
  },
  computed: {
    id      () { return this.template.id },
    primary () { return this.template.primaryDefault || this.template.primary || '#dc2626' },
    bg      () {
      const map = {
        'classico':            '#09090b',
        'minimalista':         '#1c1917',
        'moda-boutique':       '#0a0805',
        'moda-editorial':      '#09090b',
        'restaurante-bistro':  '#fdf6ec',
        'restaurante-moderno': '#09090b',
        'tech-store':          '#020617',
        'vibrante':            '#09090b',
        'natureza':            '#051a0a',
        'luxo-premium':        '#030303',
        'desporto':            '#0a0a0a',
      }
      return map[this.id] || '#111113'
    },
  },
}
</script>

<style scoped>
.mini-root {
  position: relative;
  width: 100%;
  height: 100%;
  overflow: hidden;
  font-family: 'DM Sans', sans-serif;
  color: #fff;
}
.abs { position: absolute; inset: 0; }
.stripe {
  background: repeating-linear-gradient(
    135deg,
    rgba(255,255,255,0.04) 0px,
    rgba(255,255,255,0.04) 10px,
    rgba(255,255,255,0.01) 10px,
    rgba(255,255,255,0.01) 20px
  ) !important;
}
.stripe.light {
  background: repeating-linear-gradient(
    135deg,
    rgba(180,180,180,0.12) 0px,
    rgba(180,180,180,0.12) 10px,
    rgba(180,180,180,0.03) 10px,
    rgba(180,180,180,0.03) 20px
  ) !important;
}
@keyframes marquee-mini {
  0%   { transform: translateX(0); }
  100% { transform: translateX(-50%); }
}
.marquee-strip { animation: marquee-mini 6s linear infinite; }
</style>
