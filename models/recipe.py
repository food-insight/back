from app.extensions import db

class Recipe(db.Model):
    __tablename__ = 'recipes'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(255), nullable=False)  # 레시피 이름
    ingredients = db.Column(db.Text, nullable=False)  # 재료 (JSON 형식 저장)
    instructions = db.Column(db.Text, nullable=False)  # 조리법
    created_at = db.Column(db.DateTime, server_default=db.func.now())  # 생성 시간

    def to_dict(self):
        """JSON 직렬화를 위한 메서드"""
        return {
            "id": self.id,
            "title": self.title,
            "ingredients": self.ingredients.split(", "),  # 문자열을 리스트로 변환
            "instructions": self.instructions,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S")
        }
