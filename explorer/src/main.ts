export {};
type Node = {player:number; card:number; history:string; probabilities:number[]; regrets:number[]};
type State = {terminal:boolean; player?:number; actions?:string[]; labels?:string[]};
type Study = {version:number; game:string; cards:Record<string,string>; states:Record<string,State>; information_sets:Node[]; report:{exploitability:number;profile_value_player_zero:number}; always_bet_call_report:{exploitability:number}; iterations:number};
const el = (id:string) => document.getElementById(id)!;
const select = (id:string) => el(id) as HTMLSelectElement;
function validate(data:Study):Study {
  if(data.version !== 1 || data.game !== "kuhn" || data.information_sets.length !== 12) throw Error("Unsupported strategy export");
  const keys = new Set<string>();
  for(const n of data.information_sets) {
    const key = `${n.player}:${n.card}:${n.history}`;
    const s = data.states[n.history];
    if(keys.has(key) || !s || s.terminal || s.player !== n.player || !(String(n.card) in data.cards) ||
      n.probabilities.length !== 2 || n.probabilities.some(p => !Number.isFinite(p) || p<0 || p>1) ||
      Math.abs(n.probabilities.reduce((a,b)=>a+b,0)-1)>1e-9 || n.regrets.length!==2 || n.regrets.some(r=>!Number.isFinite(r))) throw Error("Invalid information set");
    keys.add(key);
  }
  return data;
}
let data:Study;
function inspect() {
  const h=select("history").value, card=Number(select("card").value);
  const s=data.states[h];
  const n=data.information_sets.find(n=>n.card===card && n.history===h)!;
  el("seat").textContent=`Player ${s.player} · ${data.cards[card]} · public history ${h || "start"}`;
  el("actions").replaceChildren();
  s.actions!.forEach((a,i)=>{
    const row=document.createElement("div"); row.className="action";
    const label=document.createElement("span"); label.textContent=`${s.labels![i]} (${a})`;
    const value=document.createElement("strong"); value.textContent=`${(n.probabilities[i]*100).toFixed(1)}%`;
    const bar=document.createElement("progress"); bar.max=1; bar.value=n.probabilities[i];
    const regret=document.createElement("small"); regret.textContent=`Cumulative regret: ${n.regrets[i].toFixed(3)}`;
    row.append(label,value,bar,regret); el("actions").append(row);
  });
  el("hidden").textContent=`The other card could be ${Object.entries(data.cards).filter(([c])=>Number(c)!==card).map(([,name])=>name).join(" or ")}. Both deals share this one policy. Public actions may change your beliefs; the policy never receives the hidden card.`;
}
let token="";
async function api(path:string, body:object):Promise<any> {
  const response=await fetch(path,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body)});
  if(!response.ok) throw Error("Action failed. Start a new hand.");
  return response.json();
}
function showHand(hand:{card:number;history:string;terminal:boolean;opponent_card?:number;payoff?:number}) {
  el("hand").textContent=`Your card: ${data.cards[hand.card]} · history: ${hand.history || "start"} · opponent: ${hand.terminal ? data.cards[hand.opponent_card!] : "hidden"}`;
  el("play-actions").replaceChildren();
  if(hand.terminal) { el("result").textContent=`Hand complete. Your net payoff: ${hand.payoff} chips.`; return; }
  el("result").textContent="You are player 0. Both players ante one chip.";
  const s=data.states[hand.history];
  s.actions!.forEach((a,i)=>{
    const button=document.createElement("button"); button.textContent=s.labels![i];
    button.onclick=async()=>{for(const b of el("play-actions").querySelectorAll("button")) b.disabled=true;
      try {showHand(await api("/api/act",{token,action:a}));} catch(e){el("result").textContent=String(e);}};
    el("play-actions").append(button);
  });
}
async function main() {
  data=validate(await (await fetch("strategy.json")).json());
  el("metrics").textContent=`${data.iterations.toLocaleString()} CFR+ iterations · exact exploitability ${data.report.exploitability.toFixed(5)} chips/hand · player 0 value ${data.report.profile_value_player_zero.toFixed(5)}`;
  el("lesson").textContent=`Always betting or calling feels strong, but its exact exploitability is ${data.always_bet_call_report.exploitability.toFixed(3)} chips/hand, compared with ${data.report.exploitability.toFixed(5)} for the saved mixture. Opponents can fold weak cards and call strong ones. Mixing checks, bets and bluffs makes your private card harder to infer. Exploitability is half the sum of both players’ best-response gains, not a promised winning rate.`;
  for(const [card,name] of Object.entries(data.cards)) select("card").add(new Option(name,card));
  for(const [h,s] of Object.entries(data.states)) if(!s.terminal) select("history").add(new Option(h || "start",h));
  select("card").onchange=inspect; select("history").onchange=inspect; inspect();
  el("new").onclick=async()=>{try{const hand=await api("/api/new",{}); token=hand.token; showHand(hand);}catch(e){el("result").textContent=String(e);}};
}
main().catch(e=>{el("metrics").textContent=`Could not load strategy: ${e}`;});
