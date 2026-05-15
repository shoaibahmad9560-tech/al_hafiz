"""
WhatsApp AI Automation + Chat Management System
Enhancement Layer — integrates with existing NestJS WhatsApp Messenger
WITHOUT breaking or replacing the existing system.

Architecture: Middleware layer that hooks into message flow via webhooks.
"""

import os
import logging
from flask import Flask, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

# ─── Logging Setup ────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.DEBUG if os.getenv("FLASK_ENV") == "development" else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("WhatsAppAI")


def create_app() -> Flask:
    """Factory function — creates and configures the Flask app."""
    from config.settings import Config

    app = Flask(__name__)
    app.config.from_object(Config)

    # ── CORS ──────────────────────────────────────────────────────────────────
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # ── Initialize all services (must happen before blueprints use them) ──────
    from services.factory import init_services
    init_services(app)
    from services.factory import get_media_service
    from services.commerce.scheduler import ReEngagementScheduler
    from services.factory import get_lead_service, get_wa_service, get_session_store
    
    _scheduler = ReEngagementScheduler(
        lead_service=get_lead_service(),
        wa_service=get_wa_service(),
        redis_client=get_session_store()._redis,
        check_interval=int(os.getenv("REENGAGE_INTERVAL", 3600))
    )
    _scheduler.start()

    # ── Register Blueprints ───────────────────────────────────────────────────
    from routes.webhook import webhook_bp
    from routes.integration import integration_bp
    from routes.broadcast import broadcast_bp
    from routes.agent import agent_bp
    from routes.status import status_bp
    # ── Al Hafiz Electronics commerce routes ──────────────────────────────────
    from routes.catalog import catalog_bp
    from routes.orders import orders_bp
    from routes.media import media_bp

    app.register_blueprint(webhook_bp,     url_prefix="/api/whatsapp")
    app.register_blueprint(integration_bp, url_prefix="/api/integration")
    app.register_blueprint(broadcast_bp,   url_prefix="/api/broadcast")
    app.register_blueprint(agent_bp,       url_prefix="/api/agents")
    app.register_blueprint(status_bp,      url_prefix="/api/status")
    # ── Commerce ───────────────────────────────────────────────────────────────
    app.register_blueprint(catalog_bp,     url_prefix="/api/catalog")
    app.register_blueprint(orders_bp,      url_prefix="/api/orders")
    app.register_blueprint(media_bp,       url_prefix="/api/media")
    from routes.events import events_bp
    app.register_blueprint(events_bp, url_prefix="/api/events")

    logger.info("✅ Al Hafiz Electronics — WhatsApp Commerce Platform ready")
    logger.info("📡 Webhook:     POST /api/whatsapp/webhook")
    logger.info("📦 Catalog:     /api/catalog/categories  /api/catalog/products")
    logger.info("🛒 Orders:      /api/orders/")
    logger.info("📢 Broadcast:   POST /api/broadcast/send")
    logger.info("🧑 Agents:      GET  /api/agents/chats")
    logger.info("💚 Status:      GET  /api/status/health")
    logger.info("🖥️  Admin Panel: GET  /admin")

    # ── Serve the Admin Panel HTML ────────────────────────────────────────────
    @app.route("/admin")
    def admin_panel():
        return send_from_directory(os.path.dirname(os.path.abspath(__file__)), "admin_panel.html")

    @app.route("/static/uploads/<path:filepath>")
    def serve_upload(filepath):
        upload_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "uploads")
        directory = os.path.dirname(os.path.join(upload_dir, filepath))
        filename = os.path.basename(filepath)
        return send_from_directory(directory, filename)

    return app


if __name__ == "__main__":
    app = create_app()
    port = int(os.getenv("AI_LAYER_PORT", 5000))
    debug = os.getenv("FLASK_ENV") == "development"
    app.run(host="0.0.0.0", port=port, debug=debug)
