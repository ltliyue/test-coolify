"""
ReceptivIQ Platform — Architecture Poster (v2, beautified)

Dark-themed multi-tenant SaaS architecture with brand logos.
Renders: architecture-poster.{png,svg}

Improvements over v1:
- All nodes use Custom() with real brand icons or letter badges
  (no empty Blank() rectangles)
- Adds 6 Phase-2 platforms from Discovery doc (Trade Desk,
  Google Ads, Salesforce, NetSuite, PlacerIQ, Experian)
- External Integrations split into "Implemented" vs "Planned"
  sub-clusters for honest TODO surfacing
- Tighter cluster grouping, fewer edge crossings

Requires: graphviz + diagrams + PIL (for badge gen)
Run: python3 _gen_badges.py && python3 architecture-poster.py
"""

from diagrams import Cluster, Diagram, Edge
from diagrams.custom import Custom
from diagrams.onprem.client import Users, User
from diagrams.onprem.analytics import Dbt

# ── Theme ─────────────────────────────────────────────────────────────────────

GRAPH_ATTR = {
    "bgcolor": "#0F172A",
    "fontcolor": "#F8FAFC",
    "fontname": "Helvetica",
    "fontsize": "26",
    "labelloc": "t",
    "pad": "1.8",
    "splines": "ortho",            # orthogonal edges = clean
    "nodesep": "0.55",
    "ranksep": "2.0",
    "compound": "true",
    "concentrate": "false",
    "rankdir": "TB",
    "ordering": "out",
    "newrank": "true",
    "dpi": "120",                  # crisp PNG at moderate file size
}

NODE_ATTR = {
    "fontcolor": "#E2E8F0",
    "fontname": "Helvetica",
    "fontsize": "12",
    "color": "transparent",
    "imagescale": "true",
    "labelloc": "b",
    "margin": "0.22,0.16",
    "fixedsize": "false",
}

EDGE_ATTR = {
    "color": "#475569",
    "fontcolor": "#94A3B8",
    "fontname": "Helvetica",
    "fontsize": "9",
    "penwidth": "1.2",
    "arrowsize": "0.7",
}


def cluster(border_hex, font_hex, label_size="14"):
    return {
        "bgcolor": "#1E293B",
        "pencolor": border_hex,
        "penwidth": "2.5",
        "fontcolor": font_hex,
        "fontsize": label_size,
        "fontname": "Helvetica bold",
        "style": "rounded",
        "labeljust": "l",
        "margin": "20",
    }


def sub_cluster(border_hex, font_hex):
    return {
        "bgcolor": "#0F172A",
        "pencolor": border_hex,
        "penwidth": "1.5",
        "fontcolor": font_hex,
        "fontsize": "11",
        "fontname": "Helvetica",
        "style": "rounded,dashed",
        "labeljust": "l",
        "margin": "12",
    }


C_USERS  = cluster("#F59E0B", "#FCD34D")
C_INTEG  = cluster("#F59E0B", "#FCD34D")
C_WH     = cluster("#A855F7", "#C4B5FD")
C_APP    = cluster("#3B82F6", "#93C5FD")
C_DATA   = cluster("#10B981", "#6EE7B7")
C_LLM    = cluster("#EC4899", "#F9A8D4")
C_MON    = cluster("#14B8A6", "#5EEAD4")
C_DEV    = cluster("#64748B", "#CBD5E1")

# Edge color hints
E_DATA   = "#A855F7"
E_APP    = "#3B82F6"
E_USER   = "#F59E0B"
E_OUT    = "#10B981"
E_AI     = "#EC4899"
E_MON    = "#14B8A6"
E_DEV    = "#64748B"

ICONS = "./icons"


def i(name: str) -> str:
    return f"{ICONS}/{name}.png"


# ─────────────────────────────────────────────────────────────────────────────
with Diagram(
    "ReceptivIQ Platform — Multi-Tenant Architecture",
    filename="architecture-poster",
    show=False,
    outformat=["png", "svg"],
    direction="TB",
    graph_attr=GRAPH_ATTR,
    node_attr=NODE_ATTR,
    edge_attr=EDGE_ATTR,
):
    # ════════════════════════ TIER 1: External World ════════════════════════
    with Cluster("  👥  USERS", graph_attr=C_USERS):
        end_users = Users("End Users\n(Brand Clients)")
        admins = User("Admins\n(Agency Staff)")

    with Cluster("  🔌  EXTERNAL DATA SOURCES  ·  15 Platforms", graph_attr=C_INTEG):
        with Cluster("Analytics & Social  (OAuth)", graph_attr=sub_cluster("#475569", "#CBD5E1")):
            ga4 = Custom("GA4", i("ga4"))
            meta = Custom("Meta Ads", i("meta"))
            hubspot = Custom("HubSpot", i("hubspot"))
            tiktok = Custom("TikTok", i("tiktok"))

        with Cluster("Programmatic / DSP  (API Key)", graph_attr=sub_cluster("#475569", "#CBD5E1")):
            dv360 = Custom("DV360", i("dv360"))
            stackadapt = Custom("StackAdapt", i("stackadapt"))
            trade_desk = Custom("Trade Desk\n(planned)", i("trade_desk"))

        with Cluster("CRM & Search  (OAuth)", graph_attr=sub_cluster("#475569", "#CBD5E1")):
            google_ads = Custom("Google Ads\n(planned)", i("googleads"))
            salesforce = Custom("Salesforce\n(planned)", i("salesforce"))
            netsuite = Custom("NetSuite\n(planned)", i("netsuite"))

        with Cluster("Identity / Attribution / Audience", graph_attr=sub_cluster("#475569", "#CBD5E1")):
            leadrx = Custom("LeadRX", i("leadrx"))
            liveramp = Custom("LiveRamp", i("liveramp"))
            quorum = Custom("Quorum", i("quorum"))
            placeriq = Custom("PlacerIQ\n(P0 planned)", i("placeriq"))
            experian = Custom("Experian\n(data feed)", i("experian"))

    # ════════════════════════ TIER 2: Data Pipeline ════════════════════════
    with Cluster("  ❄️   DATA WAREHOUSE & ELT", graph_attr=C_WH):
        airflow = Custom("Airflow\n(DAG scheduler)", i("apacheairflow"))
        snowflake = Custom("Snowflake\n(prod warehouse)", i("snowflake"))
        dbt = Dbt("dbt\n(in-warehouse\nTransform)")
        airflow >> Edge(color=E_DATA, label="schedule", style="dashed") >> snowflake
        snowflake >> Edge(color=E_DATA, label="ELT") >> dbt

    # ════════════════════════ TIER 3: Application ════════════════════════
    with Cluster("  🚀  RENDER PLATFORM  ·  Application Tier (FastAPI :8000)", graph_attr=C_APP):
        web = Custom("Web\n(React 19)", i("react"))
        auth = Custom("Auth Service\n(JWT + OAuth)", i("auth"))
        bizapi = Custom("BizAPI\n(FastAPI :8000)", i("fastapi"))
        biz_svc = Custom("Business Service\n(Campaigns · Reports)", i("biz_svc"))
        agent_svc = Custom("Agent Service\n(/api/v1/ai)", i("agent_svc"))
        brain = Custom("AI Brain\n(Persona · Creative ·\nAttribution)", i("anthropic"))
        celery = Custom("Celery Workers", i("celery"))

        web >> Edge(color=E_APP) >> auth
        web >> Edge(color=E_APP) >> bizapi
        bizapi >> Edge(color=E_APP, label="biz") >> biz_svc
        bizapi >> Edge(color=E_APP, label="AI") >> agent_svc
        agent_svc >> Edge(color=E_APP) >> brain
        bizapi >> Edge(color=E_APP, style="dashed") >> celery

    # ════════════════════════ TIER 4: Persistence + Output ════════════════════════
    with Cluster("  💾  DATA LAYER", graph_attr=C_DATA):
        neon = Custom("Neon\n(Postgres + pgvector)", i("neon"))
        redis = Custom("Redis\n(cache · broker)", i("redis"))
        s3 = Custom("S3 / MinIO\n(reports · assets)", i("aws_s3"))

    with Cluster("  🤖  LLMs", graph_attr=C_LLM):
        openrouter = Custom("OpenRouter\n(gateway)", i("openrouter"))
        bedrock = Custom("AWS Bedrock\n(HIPAA, planned)", i("bedrock"))

    with Cluster("  📊  MONITORING & EMAIL", graph_attr=C_MON):
        sentry = Custom("Sentry\n(errors)", i("sentry"))
        langfuse = Custom("Langfuse\n(LLM trace)", i("langfuse"))
        smtp = Custom("SMTP\n(email reports)", i("smtp"))

    with Cluster("  🛠️   DEVOPS", graph_attr=C_DEV):
        github = Custom("GitHub\n(source · PR · CI)", i("github"))
        docker = Custom("Docker Compose\n(local dev)", i("docker"))
        render = Custom("Render\n(prod hosting)", i("render"))

    # ════════════════════════ Inter-cluster edges ════════════════════════
    # Users → App
    end_users >> Edge(color=E_USER, label="HTTPS/WSS") >> web
    admins >> Edge(color=E_USER, label="admin") >> web

    # External sources → Airflow (data ingestion)
    ga4 >> Edge(color=E_DATA, label="OAuth + Compliance Gate") >> airflow
    meta >> Edge(color=E_DATA) >> airflow
    hubspot >> Edge(color=E_DATA) >> airflow
    tiktok >> Edge(color=E_DATA) >> airflow
    dv360 >> Edge(color=E_DATA, label="API Key") >> airflow
    stackadapt >> Edge(color=E_DATA) >> airflow
    trade_desk >> Edge(color=E_DATA, style="dashed") >> airflow
    google_ads >> Edge(color=E_DATA, style="dashed") >> airflow
    salesforce >> Edge(color=E_DATA, style="dashed") >> airflow
    netsuite >> Edge(color=E_DATA, style="dashed") >> airflow
    leadrx >> Edge(color=E_DATA) >> airflow
    liveramp >> Edge(color=E_DATA, label="bidirectional") >> airflow
    quorum >> Edge(color=E_DATA) >> airflow
    placeriq >> Edge(color=E_DATA, style="dashed") >> airflow
    experian >> Edge(color=E_DATA, style="dashed", label="CSV feed") >> airflow

    # Warehouse → App
    dbt >> Edge(color=E_DATA, style="dashed", label="SELECT marts") >> bizapi

    # App → Data Layer
    bizapi >> Edge(color=E_OUT, label="CRUD") >> neon
    bizapi >> Edge(color=E_OUT, style="dashed") >> redis
    celery >> Edge(color=E_OUT, label="files") >> s3

    # App → LLMs
    brain >> Edge(color=E_AI, label="chat completions") >> openrouter
    brain >> Edge(color=E_AI, style="dashed", label="HIPAA tenants") >> bedrock

    # Audience Activation outbound (F-21) — LiveRamp planned bypass
    biz_svc >> Edge(color=E_USER, label="audience push") >> meta
    biz_svc >> Edge(color=E_USER) >> dv360
    biz_svc >> Edge(color=E_USER, style="dashed", label="planned via\nLiveRamp") >> liveramp

    # App → Monitoring
    bizapi >> Edge(color=E_MON, style="dashed", label="errors") >> sentry
    brain >> Edge(color=E_MON, style="dashed", label="LLM trace") >> langfuse
    celery >> Edge(color=E_MON, style="dashed", label="emails") >> smtp

    # DevOps
    github >> Edge(color=E_DEV, label="deploy") >> render
    github >> Edge(color=E_DEV, style="dashed") >> docker
