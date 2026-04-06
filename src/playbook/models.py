class Playbook(Base):
    """Stores automated workflows and execution rules."""
    __tablename__ = "playbooks"

    playbook_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(String(500))
    
    # A JSON structure defining WHEN this playbook runs 
    # e.g., {"trigger_on": "severity == critical", "source_tool": "Firewall"}
    trigger_conditions = Column(JSON, nullable=False) 
    
    # A JSON array defining WHAT the playbook does 
    # e.g., [{"action": "isolate_network", "target": "source_ip"}, {"action": "email_admin"}]
    action_steps = Column(JSON, nullable=False)
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())