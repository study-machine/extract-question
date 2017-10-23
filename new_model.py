


class MissonGroup(object):
	"""课程关卡，6道题为一关(组)"""
	def __init__(self, q_type):
		self.q_type = q_type
		self.order = -1
		self.course_id = -1
		self.questions = []

		# 数量应为6
		self.count = 0