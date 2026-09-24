import Link from "next/link";

function AerialSystem() {
  return (
    <figure className="aerial" aria-label="YardOS live site model showing an industrial yard with detected assets and a drone scan path">
      <svg viewBox="0 0 1200 690" role="img" aria-hidden="true">
        <defs>
          <pattern id="grain" width="8" height="8" patternUnits="userSpaceOnUse"><circle cx="1" cy="1" r=".7" fill="#fff" opacity=".04"/></pattern>
          <pattern id="roof" width="28" height="28" patternUnits="userSpaceOnUse"><path d="M0 28 28 0" stroke="#fff" strokeOpacity=".035"/></pattern>
          <filter id="soft"><feGaussianBlur stdDeviation="9"/></filter>
        </defs>
        <rect width="1200" height="690" fill="#252a25"/>
        <path d="M0 72h1200M0 566h1200M378 0v690M993 0v690" stroke="#8f988c" strokeWidth="56" opacity=".17"/>
        <path d="M0 90h1200M0 548h1200M396 0v690M975 0v690" stroke="#111410" strokeWidth="2" strokeDasharray="26 24" opacity=".65"/>
        <g fill="#3b413a" stroke="#545b51" strokeWidth="2"><path d="M58 142h280v174H58z"/><path d="M445 115h460v218H445z"/><path d="M1018 130h126v247h-126z"/><path d="M55 403h274v106H55z"/><path d="M446 432h206v79H446z"/><path d="M713 393h194v128H713z"/></g>
        <g fill="url(#roof)" opacity=".8"><path d="M58 142h280v174H58z"/><path d="M445 115h460v218H445z"/><path d="M55 403h274v106H55z"/></g>
        <g fill="#777c70" opacity=".75">
          {Array.from({length:13}).map((_,i)=><rect key={`a${i}`} x={472+i*31} y="358" width="20" height="72" rx="2"/>)}
          {Array.from({length:7}).map((_,i)=><rect key={`b${i}`} x={90+i*34} y="338" width="22" height="51" rx="2"/>)}
          {Array.from({length:8}).map((_,i)=><rect key={`c${i}`} x={1026+(i%3)*36} y={410+Math.floor(i/3)*58} width="22" height="43" rx="2"/>)}
        </g>
        <path d="M151 625C215 542 316 586 409 501S585 389 676 475 841 610 1067 560" fill="none" stroke="#b8c68c" strokeWidth="2" strokeDasharray="9 9" opacity=".7"/>
        <path d="M39 53h1120v574H39z" fill="none" stroke="#b8c68c" strokeWidth="1.5" strokeDasharray="14 10" opacity=".55"/>
        <g className="detections" fill="none" stroke="#d5dfb1" strokeWidth="2"><rect x="562" y="355" width="26" height="79"/><rect x="748" y="387" width="30" height="94"/><rect x="121" y="332" width="28" height="61"/><rect x="1049" y="460" width="29" height="52"/><rect x="819" y="538" width="38" height="20"/><rect x="330" y="541" width="36" height="20"/></g>
        <g fill="#070807" stroke="#d5dfb1" strokeWidth="1"><circle cx="676" cy="475" r="11"/><path d="M663 475h26M676 462v26"/></g>
        <g className="map-labels" fill="#e5e9df"><text x="560" y="347">TRAILER-018 · DWELL 02:14:31</text><text x="748" y="379">TRK-042 · 37.4 KM/H</text><text x="816" y="531">VEHICLE-091 · MOVING</text><text x="53" y="45">MISSION BOUNDARY / SITE 01</text></g>
        <rect width="1200" height="690" fill="url(#grain)"/><ellipse cx="785" cy="530" rx="180" ry="90" fill="#b8c68c" opacity=".025" filter="url(#soft)"/>
      </svg>
      <figcaption className="aerial-top"><span><i/> MISSION ACTIVE</span><span>CAPTURE 0042</span><span className="coord">29.7604° N&nbsp;&nbsp; 95.3698° W</span></figcaption>
      <div className="aerial-bottom"><span>LIVE SITE MODEL</span><span>14:32:08 / UTC−05</span></div>
    </figure>
  );
}

const pipeline = [
  ["CAPTURE","Autonomous aerial systems continuously observe the site."],
  ["MAP","Imagery becomes geographically accurate representations of the environment."],
  ["UNDERSTAND","YardOS identifies objects, movement, and physical change."],
  ["ACT","Operators receive structured intelligence instead of raw footage."],
];

const capabilities = [
  ["PERCEPTION","Detect and classify physical objects from aerial imagery."],
  ["CHANGE","Understand what appeared, disappeared, or moved between captures."],
  ["TRACKING","Build spatial histories of vehicles, equipment, and assets."],
  ["AUTONOMY","Plan and coordinate aerial data collection."],
  ["WORLD MODEL","Maintain a continuously updated representation of the physical site."],
];

function ProductExperience(){return <div className="product-ui">
  <div className="product-map">
    <div className="map-bar"><span><i/> LIVE SITE MODEL</span><span>CAPTURE / 0042</span></div>
    <svg viewBox="0 0 900 600" aria-hidden="true"><rect width="900" height="600" fill="#20251f"/><g fill="#393f38" stroke="#60675d"><path d="M28 52h258v172H28zM360 52h330v190H360zM726 48h140v258H726zM28 302h280v126H28zM360 324h194v110H360zM594 306h272v132H594z"/></g><g fill="#72776b">{Array.from({length:15}).map((_,i)=><rect key={i} x={48+(i%5)*47} y={250+Math.floor(i/5)*55} width="24" height="42"/>)}</g><path d="M79 530C180 455 246 514 354 426S564 310 792 480" fill="none" stroke="#b8c68c" strokeWidth="2" strokeDasharray="8 8"/><g fill="none" stroke="#d9e0c4" strokeWidth="2"><rect x="486" y="269" width="31" height="70"/><rect x="622" y="453" width="42" height="24"/><rect x="193" y="450" width="39" height="22"/><rect x="734" y="324" width="28" height="74"/></g><circle cx="354" cy="426" r="8" fill="#070807" stroke="#d9e0c4"/></svg>
    <div className="timeline"><span>13:58</span><i/><b/><i/><i/><span>14:32</span></div>
  </div>
  <aside className="product-panel"><p>SITE 01</p><h3>Operational overview</h3><dl><div><dt>Assets</dt><dd>137</dd></div><div><dt>Vehicles</dt><dd>24</dd></div><div><dt>Trailers</dt><dd>83</dd></div><div><dt>Changes</dt><dd>18</dd></div></dl><article><span>RECENT EVENT</span><strong>TRAILER-031</strong><p>Moved 84 m</p><small>LAST OBSERVED&nbsp;&nbsp; 14:21:08</small></article><em>ILLUSTRATIVE PRODUCT VIEW</em></aside>
  </div>}

export default function Home() {
  return <main className="landing">
    <header className="site-nav"><Link className="wordmark" href="#top" aria-label="YardOS home">YARDOS</Link><nav aria-label="Primary navigation"><Link href="#system">SYSTEM</Link><Link href="#vision">VISION</Link><a href="mailto:mg188@rice.edu">CONTACT</a></nav></header>
    <section className="hero" id="top">
      <div className="hero-copy"><p className="eyebrow">YARDOS / 01</p><h1>Intelligence for the<br/>physical world.</h1><p className="dek">YardOS turns autonomous aerial systems into persistent intelligence for industrial sites.</p><div className="hero-actions"><Link className="button primary" href="#system">VIEW THE SYSTEM <span>↘</span></Link><a className="button text" href="mailto:mg188@rice.edu">CONTACT</a></div><a className="hero-email" href="mailto:mg188@rice.edu">mg188@rice.edu</a></div>
      <AerialSystem/>
      <div className="scroll-cue"><span>SCROLL TO EXPLORE</span><i/></div>
    </section>
    <section className="section flow" id="system"><div className="section-kicker">OBSERVATION / 02</div><h2>From imagery<br/>to understanding.</h2><div className="pipeline">{pipeline.map(([title,copy],i)=><article key={title}><span>0{i+1}</span><h3>{title}</h3><p>{copy}</p>{i<pipeline.length-1&&<b>→</b>}</article>)}</div></section>
    <section className="section architecture"><div className="section-kicker">SYSTEM / 03</div><div className="split-head"><h2>One system.<br/>Every layer.</h2><p>YardOS connects aerial autonomy to the operational decisions that happen on the ground.</p></div><div className="architecture-stack"><article><span>INPUT</span><h3>DRONES</h3><p>Aerial capture</p></article><i>↓</i><article><span>01 / AUTONOMY</span><h3>YARDOS AUTONOMY</h3><p>Mission planning&nbsp;&nbsp; Fleet orchestration&nbsp;&nbsp; Telemetry</p></article><i>↓</i><article><span>02 / PERCEPTION</span><h3>YARDOS PERCEPTION</h3><p>Detection&nbsp;&nbsp; Segmentation&nbsp;&nbsp; Tracking&nbsp;&nbsp; Change detection</p></article><i>↓</i><article><span>03 / WORLD MODEL</span><h3>YARDOS WORLD MODEL</h3><p>Assets&nbsp;&nbsp; Locations&nbsp;&nbsp; Movement&nbsp;&nbsp; History</p></article><i>↓</i><article><span>OUTPUT</span><h3>OPERATIONS</h3><p>Inventory&nbsp;&nbsp; Security&nbsp;&nbsp; Inspection&nbsp;&nbsp; Logistics&nbsp;&nbsp; Infrastructure</p></article></div></section>
    <section className="section experience"><div className="section-kicker">PRODUCT / 04</div><div className="split-head"><h2>Reality becomes<br/>queryable.</h2><p>A live spatial interface transforms each capture into objects, movement, and change—not another folder of footage.</p></div><ProductExperience/></section>
    <section className="section capability"><div className="section-kicker">CAPABILITIES / 05</div><div className="cap-list">{capabilities.map(([title,copy],i)=><article key={title}><span>{String(i+1).padStart(2,"0")}</span><h3>{title}</h3><p>{copy}</p></article>)}</div></section>
    <section className="vision" id="vision"><div className="section-kicker">VISION / 06</div><h2>The physical world should be<br/>as observable as software.</h2><div className="vision-copy"><p>Modern businesses have extraordinary visibility into their digital systems and remarkably little visibility into their physical operations.</p><p>YardOS is building the infrastructure to change that.</p><p>Autonomous aerial systems observe the world. YardOS turns those observations into a persistent, machine-readable model of reality.</p></div></section>
    <section className="technical"><p>One software layer from sensor to decision.</p><div>{["AUTONOMOUS SYSTEMS","GEOSPATIAL DATA","PERCEPTION","TEMPORAL UNDERSTANDING","WORLD MODEL","OPERATIONS"].map((x,i)=><span key={x}>{x}{i<5&&<b>→</b>}</span>)}</div></section>
    <section className="section industries"><div className="section-kicker">APPLICATIONS / 07</div><h2>Built for environments<br/>that never stop changing.</h2><div>{["LOGISTICS","CONSTRUCTION","ENERGY","INFRASTRUCTURE","INDUSTRIAL SITES"].map((x,i)=><span key={x}><b>0{i+1}</b>{x}</span>)}</div><small>Target applications</small></section>
    <section className="final-cta"><div className="section-kicker">CONTACT / 08</div><h2>Build a live understanding<br/>of the physical world.</h2><p>Investors, operators, and engineers:</p><a href="mailto:mg188@rice.edu">mg188@rice.edu</a><a className="button primary" href="mailto:mg188@rice.edu">GET IN TOUCH <span>↗</span></a></section>
    <footer><b>YARDOS</b><span>SAN FRANCISCO, CA</span><a href="mailto:mg188@rice.edu">mg188@rice.edu</a><span>© 2026 YardOS</span></footer>
  </main>
}
