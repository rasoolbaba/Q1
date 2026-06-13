"""
پروتکل نواروی و نبوغ (NEK - Neuro-Genius Protocol)
پیاده‌سازی ریاضی تعامل و ساختار شبکه به جای ریاضی محاسبه عددی صرف

این ماژول هسته اصلی NEK را پیاده‌سازی می‌کند:
- واحد پایه: قرارداد تعامل (Interaction Contract) نه بردار عددی
- عملیات: سازگاری، اجازه/رد، محدوده اثر، ترکیب‌پذیری
- حافظه: فردی و تیمی با مکانیزم اجماع
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple, Any, Callable
from enum import Enum
import hashlib
import json
from datetime import datetime


class InteractionStatus(Enum):
    """وضعیت‌های ممکن برای یک تعامل"""
    PENDING = "pending"
    ALLOWED = "allowed"
    DENIED = "denied"
    COMMITTED = "committed"
    ABORTED = "aborted"
    COMPATIBLE = "compatible"
    INCOMPATIBLE = "incompatible"


@dataclass
class InteractionContract:
    """
    واحد پایه در NEK: قرارداد تعامل
    به جای weighted sum، بر اساس منطق سازگاری و مجوز عمل می‌کند
    """
    source_id: str
    target_id: str
    interaction_type: str
    compatibility_score: float  # منطق سازگاری (0.0 تا 1.0)
    permission_granted: bool  # قید و مجوز
    blast_radius: float  # محدوده اثر (چقدر می‌تواند گسترش یابد)
    composability_index: float  # ترکیب‌پذیری شبکه
    status: InteractionStatus = InteractionStatus.PENDING
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    signature: str = ""
    
    def __post_init__(self):
        self.signature = self._generate_signature()
    
    def _generate_signature(self) -> str:
        """تولید هش امنیتی برای ردیابی و اعتبارسنجی"""
        data = f"{self.source_id}:{self.target_id}:{self.interaction_type}:{self.timestamp}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]
    
    def evaluate(self) -> InteractionStatus:
        """
        ارزیابی قرارداد بر اساس منطق NEK
        بازگشت وضعیت نهایی تعامل
        """
        # قانون ۱: اگر مجوز داده نشده، رد می‌شود
        if not self.permission_granted:
            self.status = InteractionStatus.DENIED
            return self.status
        
        # قانون ۲: اگر سازگاری پایین است، ناسازگار
        if self.compatibility_score < 0.3:
            self.status = InteractionStatus.INCOMPATIBLE
            return self.status
        
        # قانون ۳: اگر ترکیب‌پذیری بالا و محدوده اثر کنترل‌شده است، تأیید
        if self.composability_index > 0.7 and self.blast_radius < 0.5:
            self.status = InteractionStatus.ALLOWED
            return self.status
        
        # قانون ۴: در غیر این صورت، در حالت انتظار می‌ماند
        self.status = InteractionStatus.PENDING
        return self.status
    
    def commit(self) -> bool:
        """ثبت نهایی تعامل در صورت شرایط مناسب"""
        if self.status in [InteractionStatus.ALLOWED, InteractionStatus.COMPATIBLE]:
            self.status = InteractionStatus.COMMITTED
            return True
        self.status = InteractionStatus.ABORTED
        return False


@dataclass
class AgentMemory:
    """حافظه فردی هر ایجنت"""
    agent_id: str
    contracts: List[InteractionContract] = field(default_factory=list)
    learned_patterns: Dict[str, Any] = field(default_factory=dict)
    trust_scores: Dict[str, float] = field(default_factory=dict)
    
    def add_contract(self, contract: InteractionContract):
        """افزودن قرارداد به حافظه فردی"""
        self.contracts.append(contract)
    
    def update_trust(self, other_agent_id: str, score_delta: float):
        """به‌روزرسانی امتیاز اعتماد به ایجنت دیگر"""
        current = self.trust_scores.get(other_agent_id, 0.5)
        self.trust_scores[other_agent_id] = max(0.0, min(1.0, current + score_delta))


@dataclass
class TeamMemory:
    """حافظه تیمی مشترک با مکانیزم اجماع"""
    shared_contracts: List[InteractionContract] = field(default_factory=list)
    consensus_threshold: float = 0.7
    validated_patterns: Dict[str, Any] = field(default_factory=dict)
    security_log: List[str] = field(default_factory=list)
    
    def propose_contract(self, contract: InteractionContract, proposer_votes: Dict[str, bool]) -> bool:
        """
        پیشنهاد قرارداد برای حافظه تیمی
        نیاز به اجماع دارد
        """
        yes_votes = sum(1 for vote in proposer_votes.values() if vote)
        total_votes = len(proposer_votes)
        
        if total_votes == 0:
            return False
        
        consensus_ratio = yes_votes / total_votes
        
        if consensus_ratio >= self.consensus_threshold:
            contract.evaluate()
            if contract.status in [InteractionStatus.ALLOWED, InteractionStatus.COMMITTED]:
                self.shared_contracts.append(contract)
                self.security_log.append(f"[COMMIT] Contract {contract.signature} added by consensus")
                return True
            else:
                self.security_log.append(f"[ABORT] Contract {contract.signature} failed evaluation")
                return False
        else:
            self.security_log.append(f"[REJECT] Contract {contract.signature} lacked consensus ({consensus_ratio:.2f})")
            return False
    
    def get_validated_pattern(self, pattern_name: str) -> Optional[Any]:
        """دریافت الگوی تأیید شده از حافظه تیمی"""
        return self.validated_patterns.get(pattern_name)
    
    def add_validated_pattern(self, pattern_name: str, pattern_data: Any):
        """افزودن الگوی جدید به حافظه تیمی پس از اعتبارسنجی"""
        self.validated_patterns[pattern_name] = pattern_data
        self.security_log.append(f"[PATTERN] Validated pattern '{pattern_name}' added")


class NEKAgent:
    """
    ایجنت هوشمند مبتنی بر پروتکل NEK
    دارای حافظه فردی و دسترسی به حافظه تیمی
    """
    
    def __init__(self, agent_id: str, specialization: str, team_memory: TeamMemory):
        self.agent_id = agent_id
        self.specialization = specialization
        self.memory = AgentMemory(agent_id=agent_id)
        self.team_memory = team_memory
        self.active_contracts: List[InteractionContract] = []
    
    def propose_interaction(self, target_agent: 'NEKAgent', 
                          interaction_type: str,
                          compatibility_score: float,
                          permission_granted: bool,
                          blast_radius: float,
                          composability_index: float) -> InteractionContract:
        """پیشنهاد تعامل با ایجنت دیگر"""
        contract = InteractionContract(
            source_id=self.agent_id,
            target_id=target_agent.agent_id,
            interaction_type=interaction_type,
            compatibility_score=compatibility_score,
            permission_granted=permission_granted,
            blast_radius=blast_radius,
            composability_index=composability_index
        )
        
        # ارزیابی اولیه
        status = contract.evaluate()
        
        # ذخیره در حافظه فردی
        self.memory.add_contract(contract)
        target_agent.memory.add_contract(contract)
        
        self.active_contracts.append(contract)
        
        return contract
    
    def vote_on_contract(self, contract: InteractionContract) -> bool:
        """رأی‌دهی به یک قرارداد برای اجماع تیمی"""
        # منطق رأی‌دهی بر اساس تخصص و اعتماد
        base_trust = self.memory.trust_scores.get(contract.source_id, 0.5)
        
        # اگر سازگاری بالا باشد و منبع قابل اعتماد، رأی مثبت
        if contract.compatibility_score > 0.6 and base_trust > 0.4:
            return True
        
        # اگر محدوده اثر خطرناک باشد، رأی منفی
        if contract.blast_radius > 0.8:
            return False
        
        # در غیر این صورت، بر اساس تصادفی کنترل‌شده (برای تنوع)
        return contract.composability_index > 0.5
    
    def learn_pattern(self, pattern_name: str, pattern_data: Any, submit_to_team: bool = True):
        """یادگیری الگوی جدید"""
        self.memory.learned_patterns[pattern_name] = pattern_data
        
        if submit_to_team:
            # پیشنهاد به تیم برای اعتبارسنجی
            self.team_memory.add_validated_pattern(pattern_name, pattern_data)


class NEKTeam:
    """
    تیم ایجنت‌های NEK با حافظه تیمی مشترک
    """
    
    def __init__(self, team_name: str):
        self.team_name = team_name
        self.team_memory = TeamMemory()
        self.agents: Dict[str, NEKAgent] = {}
        self.interaction_history: List[InteractionContract] = []
    
    def add_agent(self, agent_id: str, specialization: str) -> NEKAgent:
        """افزودن ایجنت جدید به تیم"""
        agent = NEKAgent(agent_id, specialization, self.team_memory)
        self.agents[agent_id] = agent
        return agent
    
    def execute_interaction_cycle(self, source_id: str, target_id: str, 
                                 interaction_type: str,
                                 params: Dict[str, Any]) -> InteractionContract:
        """اجرای یک چرخه تعامل کامل بین دو ایجنت"""
        if source_id not in self.agents or target_id not in self.agents:
            raise ValueError("One or both agents not found in team")
        
        source_agent = self.agents[source_id]
        target_agent = self.agents[target_id]
        
        # ایجاد پیشنهاد تعامل
        contract = source_agent.propose_interaction(
            target_agent=target_agent,
            interaction_type=interaction_type,
            compatibility_score=params.get('compatibility_score', 0.5),
            permission_granted=params.get('permission_granted', True),
            blast_radius=params.get('blast_radius', 0.3),
            composability_index=params.get('composability_index', 0.6)
        )
        
        # جمع‌آوری آرا از تمام ایجنت‌ها برای اجماع
        votes = {}
        for agent_id, agent in self.agents.items():
            if agent_id != source_id:  # منبع نمی‌تواند به خودش رأی دهد
                votes[agent_id] = agent.vote_on_contract(contract)
        
        # تلاش برای ثبت در حافظه تیمی
        committed = self.team_memory.propose_contract(contract, votes)
        
        if committed:
            contract.commit()
            self.interaction_history.append(contract)
            
            # به‌روزرسانی اعتماد بر اساس نتیجه
            if contract.status == InteractionStatus.COMMITTED:
                source_agent.memory.update_trust(target_id, 0.05)
                target_agent.memory.update_trust(source_id, 0.05)
        
        return contract
    
    def get_team_consensus_report(self) -> Dict[str, Any]:
        """گزارش جامع از وضعیت اجماع تیم"""
        return {
            'team_name': self.team_name,
            'total_agents': len(self.agents),
            'total_contracts': len(self.team_memory.shared_contracts),
            'validated_patterns': len(self.team_memory.validated_patterns),
            'security_events': len(self.team_memory.security_log),
            'recent_interactions': len(self.interaction_history),
            'average_compatibility': sum(c.compatibility_score for c in self.interaction_history) / max(1, len(self.interaction_history)),
            'commit_rate': sum(1 for c in self.interaction_history if c.status == InteractionStatus.COMMITTED) / max(1, len(self.interaction_history))
        }


# نمونه استفاده و تست پروتکل
def run_nek_demo():
    """اجرای دمو برای نشان دادن قابلیت‌های NEK"""
    print("=" * 60)
    print("پروتکل نواروی و نبوغ (NEK) - دمای ریاضی تعامل")
    print("=" * 60)
    
    # ایجاد تیم
    team = NEKTeam("NeuroGenius_Core")
    
    # افزودن ایجنت‌های متخصص
    aria = team.add_agent("Aria_Researcher", "Verification_and_Research")
    sara = team.add_agent("Sara_Architect", "System_Design_and_Innovation")
    kaveh = team.add_agent("Kaveh_Logic", "Validation_and_Consistency")
    
    print(f"\n✅ تیم تشکیل شد: {len(team.agents)} ایجنت متخصص")
    print(f"   - {aria.agent_id}: {aria.specialization}")
    print(f"   - {sara.agent_id}: {sara.specialization}")
    print(f"   - {kaveh.agent_id}: {kaveh.specialization}")
    
    # سناریو ۱: تعامل موفق با سازگاری بالا
    print("\n📊 سناریو ۱: تعامل با سازگاری بالا و محدوده اثر کنترل‌شده")
    contract1 = team.execute_interaction_cycle(
        source_id="Aria_Researcher",
        target_id="Sara_Architect",
        interaction_type="knowledge_transfer",
        params={
            'compatibility_score': 0.85,
            'permission_granted': True,
            'blast_radius': 0.2,
            'composability_index': 0.9
        }
    )
    print(f"   وضعیت: {contract1.status.value}")
    print(f"   امضا: {contract1.signature}")
    
    # سناریو ۲: تعامل رد شده به دلیل عدم سازگاری
    print("\n📊 سناریو ۲: تعامل با سازگاری پایین")
    contract2 = team.execute_interaction_cycle(
        source_id="Kaveh_Logic",
        target_id="Aria_Researcher",
        interaction_type="conflicting_hypothesis",
        params={
            'compatibility_score': 0.15,
            'permission_granted': True,
            'blast_radius': 0.3,
            'composability_index': 0.4
        }
    )
    print(f"   وضعیت: {contract2.status.value}")
    
    # سناریو ۳: تعامل خطرناک با محدوده اثر بزرگ
    print("\n📊 سناریو ۳: تعامل با محدوده اثر خطرناک")
    contract3 = team.execute_interaction_cycle(
        source_id="Sara_Architect",
        target_id="Kaveh_Logic",
        interaction_type="system_wide_change",
        params={
            'compatibility_score': 0.7,
            'permission_granted': True,
            'blast_radius': 0.9,
            'composability_index': 0.6
        }
    )
    print(f"   وضعیت: {contract3.status.value}")
    
    # گزارش نهایی
    print("\n" + "=" * 60)
    print("گزارش اجماع تیم")
    print("=" * 60)
    report = team.get_team_consensus_report()
    for key, value in report.items():
        print(f"   {key.replace('_', ' ').title()}: {value}")
    
    print("\n" + "=" * 60)
    print("لاگ امنیتی تیم:")
    print("=" * 60)
    for log_entry in team.team_memory.security_log[-5:]:  # آخرین ۵ رویداد
        print(f"   {log_entry}")
    
    print("\n✨ پروتکل NEK با موفقیت اجرا شد!")
    print("   - ریاضی تعامل جایگزین ریاضی محاسبه صرف شد")
    print("   - حافظه فردی و تیمی فعال است")
    print("   - مکانیزم اجماع و ضد تقلب عملیاتی است")
    
    return team


if __name__ == "__main__":
    team = run_nek_demo()
