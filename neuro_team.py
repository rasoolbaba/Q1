"""
پروتکل نواروی و نبوغ (Neuro-Genius Protocol) - پیاده‌سازی تیم ایجنتی
این سیستم دارای حافظه فردی و تیمی، مکانیزم ضد هزیان و ضد تقلب است.
"""

import json
import hashlib
import time
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum

# --- بخش ۱: ساختارهای داده‌ای و پروتکل‌ها ---

class VerificationStatus(Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"  # ضد هزیان: رد اطلاعات غیرموثق
    FLAGGED = "flagged"    # ضد تقلب: مشکوک به سرقت یا تکرار

@dataclass
class MemoryEntry:
    content: str
    timestamp: float
    source_agent_id: str
    verification_status: VerificationStatus = VerificationStatus.PENDING
    confidence_score: float = 0.0
    tags: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            "content": self.content,
            "timestamp": self.timestamp,
            "source_agent_id": self.source_agent_id,
            "status": self.verification_status.value,
            "confidence": self.confidence_score,
            "tags": self.tags
        }

class IndividualMemory:
    """حافظه خصوصی هر ایجنت برای تجربیات و مهارت‌های خاص خود"""
    def __init__(self, agent_id: str, capacity: int = 100):
        self.agent_id = agent_id
        self.capacity = capacity
        self.short_term: List[MemoryEntry] = []
        self.long_term: List[MemoryEntry] = []
        self.skills: Dict[str, float] = {}  # مهارت‌ها و سطح تسلط

    def add_experience(self, content: str, tags: List[str], is_critical: bool = False):
        entry = MemoryEntry(
            content=content,
            timestamp=time.time(),
            source_agent_id=self.agent_id,
            verification_status=VerificationStatus.VERIFIED, # تجربه شخصی همیشه معتبر است
            confidence_score=1.0,
            tags=tags
        )
        if is_critical:
            self.long_term.append(entry)
            if len(self.long_term) > self.capacity:
                self.long_term.pop(0) # مدیریت ظرفیت
        else:
            self.short_term.append(entry)
            if len(self.short_term) > self.capacity:
                self.short_term.pop(0)
        
        print(f"[حافظه فردی {self.agent_id}] تجربه جدید ثبت شد: {content[:50]}...")

    def get_context(self, query: str) -> str:
        # بازیابی مرتبط‌ترین خاطرات (شبیه‌سازی ساده)
        relevant = [e for e in self.short_term + self.long_term if query.lower() in e.content.lower()]
        if not relevant:
            return "هیچ تجربه مستقیمی یافت نشد."
        return "\n".join([f"- {e.content}" for e in relevant[-5:]])

class TeamHiveMind:
    """حافظه مشترک تیم: منبع حقیقت واحد برای جلوگیری از هزیان و تضاد"""
    def __init__(self):
        self.knowledge_base: List[MemoryEntry] = []
        self.consensus_log: List[Dict] = []
        self.security_hash = ""

    def propose_knowledge(self, entry: MemoryEntry) -> bool:
        """پروتکل ضد هزیان: پیشنهاد دانش جدید نیاز به اعتبارسنجی دارد"""
        # شبیه‌سازی فرآیند اعتبارسنجی
        if len(entry.content) < 5:
            entry.verification_status = VerificationStatus.REJECTED
            return False
        
        # محاسبه امتیاز اطمینان اولیه
        entry.confidence_score = 0.8 
        entry.verification_status = VerificationStatus.VERIFIED
        
        self.knowledge_base.append(entry)
        self._update_security_hash()
        print(f"[حافظه تیمی] دانش جدید تایید شد: {entry.content[:50]}...")
        return True

    def verify_fact(self, statement: str) -> VerificationStatus:
        """بررسی صحت یک ادعا نسبت به دانش موجود (ضد هزیان)"""
        for entry in self.knowledge_base:
            if statement.lower() in entry.content.lower() and entry.verification_status == VerificationStatus.VERIFIED:
                return VerificationStatus.VERIFIED
        # اگر در پایگاه دانش نباشد، فعلاً پرچم‌گذاری می‌شود تا توسط تیم بررسی شود
        return VerificationStatus.FLAGGED

    def _update_security_hash(self):
        """پروتکل ضد تقلب: ایجاد هش زنجیره‌ای برای اطمینان از دست‌نخورده بودن داده‌ها"""
        data = json.dumps([e.to_dict() for e in self.knowledge_base], sort_keys=True)
        self.security_hash = hashlib.sha256(data.encode()).hexdigest()

    def get_collective_wisdom(self, topic: str) -> List[str]:
        results = [e.content for e in self.knowledge_base if topic.lower() in e.content.lower()]
        return results

# --- بخش ۲: کلاس ایجنت نواروی (Neuro-Agent) ---

class NeuroAgent:
    def __init__(self, name: str, role: str, hive_mind: TeamHiveMind):
        self.name = name
        self.role = role
        self.id = hashlib.md5(name.encode()).hexdigest()[:8]
        self.hive_mind = hive_mind
        self.memory = IndividualMemory(self.id)
        self.current_task = None
        
        # تعریف مهارت‌های اولیه بر اساس نقش (نبوغ تخصصی)
        if "researcher" in role.lower():
            self.memory.skills["analysis"] = 0.95
            self.memory.skills["fact_checking"] = 0.99
        elif "architect" in role.lower():
            self.memory.skills["design"] = 0.98
            self.memory.skills["innovation"] = 0.90
        elif "critic" in role.lower():
            self.memory.skills["logic"] = 0.99
            self.memory.skills["anti_hallucination"] = 1.0

    def think(self, prompt: str) -> str:
        """فرآیند تفکر: ترکیب حافظه فردی، دانش تیمی و نقش تخصصی"""
        # 1. بازیابی زمینه از حافظه فردی
        personal_context = self.memory.get_context(prompt)
        
        # 2. بازیابی حقایق تایید شده از حافظه تیمی
        team_facts = self.hive_mind.get_collective_wisdom(prompt)
        
        # 3. تولید پاسخ (شبیه‌سازی منطق نواروی)
        response = f"[{self.name} ({self.role})]: بر اساس تحلیل من...\n"
        if team_facts:
            response += f"حقایق تایید شده تیم: {' | '.join(team_facts)}\n"
        if personal_context != "هیچ تجربه مستقیمی یافت نشد.":
            response += f"تجربیات شخصی من: {personal_context}\n"
        
        response += f"نتیجه‌گیری نوآورانه: راه‌حل پیشنهادی برای '{prompt}' با رویکرد {self.role}."
        
        # ذخیره تعامل در حافظه فردی
        self.memory.add_experience(f"پاسخ به: {prompt}", ["task", "response"])
        
        return response

    def contribute_to_team(self, new_knowledge: str):
        """اشتراک‌گذاری دانش جدید با تیم (با فیلتر ضد هزیان)"""
        entry = MemoryEntry(
            content=new_knowledge,
            timestamp=time.time(),
            source_agent_id=self.id,
            tags=[self.role, "discovery"]
        )
        success = self.hive_mind.propose_knowledge(entry)
        if success:
            print(f"✅ {self.name} دانش جدیدی به خرد جمعی افزود.")
        else:
            print(f"❌ {self.name}: پیشنهاد دانش رد شد (عدم انطباق با پروتکل).")

# --- بخش ۳: اجرای تیم و سناریوی نمونه ---

def run_neuro_team_simulation():
    print("🚀 شروع شبیه‌سازی تیم نواروی با پروتکل ضد تقلب و ضد هزیان...\n")
    
    # ایجاد مغز متفکر تیم
    team_brain = TeamHiveMind()
    
    # تعریف اعضای تیم با نقش‌های متمایز
    agent_researcher = NeuroAgent("آریا", "پژوهشگر ارشد و راستی‌آزمایی", team_brain)
    agent_architect = NeuroAgent("سارا", "معمار سیستم و نوآور", team_brain)
    agent_critic = NeuroAgent("کاوه", "ناقد منطقی و ضد هزیان", team_brain)
    
    team = [agent_researcher, agent_architect, agent_critic]
    
    # گام ۱: یادگیری اولیه (تزریق دانش پایه به حافظه تیمی)
    print("--- مرحله ۱: کالیبراسیون دانش پایه ---")
    agent_researcher.contribute_to_team("الگوریتم‌های جستجوی عمیق برای بهینه‌سازی لازم هستند.")
    agent_architect.contribute_to_team("معماری ما باید ماژولار و مبتنی بر رویداد باشد.")
    
    # گام ۲: حل مسئله collaboratively
    print("\n--- مرحله ۲: طوفان فکری برای طراحی یک سیستم جدید ---")
    task = "طراحی یک موتور پیشنهاد دهنده عصبی"
    
    for agent in team:
        print(f"\n💭 در حال تفکر {agent.name}...")
        thought = agent.think(task)
        print(thought)
        
        # شبیه‌سازی استخراج یک نکته کلیدی برای اشتراک‌گذاری
        if "معمار" in agent.role:
            agent.contribute_to_team("استفاده از گراف‌های دانش برای اتصال داده‌ها در موتور پیشنهاد دهنده ضروری است.")
        elif "ناقد" in agent.role:
            # تست پروتکل ضد هزیان
            fake_fact = "هوش مصنوعی می‌تواند بدون داده آموزش ببیند."
            status = team_brain.verify_fact(fake_fact)
            print(f"🛡️ بررسی حقیقت توسط {agent.name}: ادعای '{fake_fact}' وضعیت {status.value} دارد.")

    # گام ۳: گزارش نهایی وضعیت حافظه
    print("\n--- گزارش وضعیت نهایی ---")
    print(f"تعداد دانش‌های تایید شده در حافظه تیمی: {len(team_brain.knowledge_base)}")
    print(f"هش امنیتی حافظه تیمی (ضد تقلب): {team_brain.security_hash[:16]}...")
    
    print("\n✅ پروتکل نواروی با موفقیت اجرا شد. تیم دارای حافظه پایدار و مکانیزم ضد خطا است.")

if __name__ == "__main__":
    run_neuro_team_simulation()
