// set-risk-profile
//
// The one and only way agent_settings.risk_profile ever gets written.
// Runs server-side inside Supabase — never in the browser — so it can
// safely hold the service role key as a secret while the public dashboard
// only ever talks to it with the anon key.
//
// Deploy this via the Supabase Dashboard: Edge Functions -> Deploy a new
// function -> Via Editor -> paste this in, name it "set-risk-profile".
// Then: this function's page -> Manage -> Secrets, add:
//   SUPABASE_URL              — your project URL
//   SUPABASE_SERVICE_ROLE_KEY — the service role key (same one used in
//                                GitHub Secrets as SUPABASE_KEY)
//
// Whitelists are hardcoded on purpose — this endpoint is public (anyone
// can call it, same as anyone can view the dashboard), so it only ever
// accepts a known agent name and a known profile name, nothing else.

import { createClient } from "jsr:@supabase/supabase-js@2";

const ALLOWED_AGENTS = ["asx_bluechip_steady", "asx_smallcap_growth", "crypto_store_of_value"];
const ALLOWED_PROFILES = ["conservative", "balanced", "aggressive"];

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
};

Deno.serve(async (req: Request) => {
  if (req.method === "OPTIONS") {
    return new Response("ok", { headers: corsHeaders });
  }

  try {
    const { agent_name, risk_profile } = await req.json();

    if (!ALLOWED_AGENTS.includes(agent_name)) {
      return new Response(JSON.stringify({ error: `unknown agent: ${agent_name}` }), {
        status: 400,
        headers: { ...corsHeaders, "Content-Type": "application/json" },
      });
    }
    if (!ALLOWED_PROFILES.includes(risk_profile)) {
      return new Response(JSON.stringify({ error: `unknown profile: ${risk_profile}` }), {
        status: 400,
        headers: { ...corsHeaders, "Content-Type": "application/json" },
      });
    }

    const supabase = createClient(
      Deno.env.get("SUPABASE_URL")!,
      Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!,
    );

    const { error } = await supabase
      .from("agent_settings")
      .upsert(
        { agent_name, risk_profile, updated_at: new Date().toISOString() },
        { onConflict: "agent_name" },
      );

    if (error) throw error;

    return new Response(JSON.stringify({ ok: true, agent_name, risk_profile }), {
      headers: { ...corsHeaders, "Content-Type": "application/json" },
    });
  } catch (e) {
    return new Response(JSON.stringify({ error: String(e) }), {
      status: 500,
      headers: { ...corsHeaders, "Content-Type": "application/json" },
    });
  }
});
