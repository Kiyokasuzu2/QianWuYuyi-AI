import unittest
from src.personality.personality_adapter import PersonalityAdapter
from src.contracts import growth_schema

class TestPersonalityAdapterSkeleton(unittest.TestCase):
    def test_interface_exists(self):
        adapter = PersonalityAdapter(runtime_context=None)
        self.assertTrue(hasattr(adapter, "map_proposal_to_evolution_record"))
        self.assertTrue(hasattr(adapter, "apply_proposal"))

    def test_map_proposal_to_evolution_record_structure(self):
        ci = growth_schema.ChangeItem(path="personality.traits.shyness", before=0.1, after=0.2, reason="test")
        gp = growth_schema.GrowthProposal(source_event_id="evt_x", proposed_changes=[ci], confidence=0.8, evidence_ids=["mem1"])
        adapter = PersonalityAdapter(runtime_context=None)
        rec = adapter.map_proposal_to_evolution_record(gp)
        self.assertIn("record_id", rec)
        self.assertIn("trait_changes", rec)
        self.assertIn("shyness", rec["trait_changes"])
        self.assertIn("delta", rec["trait_changes"]["shyness"])

    def test_apply_proposal_envelope(self):
        ci = growth_schema.ChangeItem(path="personality.traits.shyness", before=0.1, after=0.2, reason="test")
        gp = growth_schema.GrowthProposal(source_event_id="evt_y", proposed_changes=[ci], confidence=0.8, evidence_ids=[])
        adapter = PersonalityAdapter(runtime_context=None)
        result = adapter.apply_proposal(gp, actor="tester")
        self.assertIsInstance(result, dict)
        self.assertIn("applied", result)
        self.assertIn("before", result)
        self.assertIn("after", result)

if __name__ == "__main__":
    unittest.main()
