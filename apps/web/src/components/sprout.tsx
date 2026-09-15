export function Sprout({className=''}:{className?:string}){
 return <svg className={className} viewBox="0 0 180 190" role="img" aria-label="Sprout, the CivicQuest companion">
  <defs><linearGradient id="sprout-body" x1="0" y1="0" x2="1" y2="1"><stop stopColor="#8dde6f"/><stop offset="1" stopColor="#00934e"/></linearGradient></defs>
  <ellipse cx="70" cy="170" rx="25" ry="8" fill="#064f32" opacity=".32"/><ellipse cx="110" cy="170" rx="25" ry="8" fill="#064f32" opacity=".32"/>
  <path d="M89 34c4-17 18-26 38-24-7 17-20 27-38 29z" fill="#b9dc62"/>
  <circle cx="90" cy="103" r="61" fill="url(#sprout-body)"/>
  <ellipse cx="28" cy="112" rx="14" ry="18" fill="#42b868"/><ellipse cx="152" cy="112" rx="14" ry="18" fill="#42b868"/>
  <circle cx="66" cy="90" r="17" fill="#fffdf3"/><circle cx="114" cy="90" r="17" fill="#fffdf3"/>
  <circle cx="70" cy="93" r="8" fill="#17251d"/><circle cx="118" cy="93" r="8" fill="#17251d"/>
  <ellipse cx="51" cy="119" rx="10" ry="6" fill="#e0aa72" opacity=".65"/><ellipse cx="129" cy="119" rx="10" ry="6" fill="#e0aa72" opacity=".65"/>
  <path d="M66 122c14 16 33 16 48 0" fill="none" stroke="#283f2d" strokeWidth="6" strokeLinecap="round"/>
 </svg>;
}
