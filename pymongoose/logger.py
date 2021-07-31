colors = {
	"red":
	   "\x1B[31m",
	"yellow":
	   "\x1B[33m",
	"green":
	   "\x1B[32m",
	"blue":
	   "\x1B[34m",
	"reset":
	   "\x1B[0m",
	None:
	   "\x1B[0m",
}

class Logger():
	@staticmethod
	def printWarn(text: str):
		print(f"{colors['yellow']}[PYMONGOOSE WARN]: {text}{colors['reset']}")

	@staticmethod
	def printLog(text: str):
		print(f"{colors['blue']}[PYMONGOOSE LOG]: {text}{colors['reset']}")

	@staticmethod
	def printError(text: str):
		print(f"{colors['red']}[PYMONGOOSE ERROR]: {text}{colors['reset']}")

	@staticmethod
	def printSuccess(text: str):
		print(f"{colors['green']}[PYMONGOOSE SUCCESS]: {text}{colors['reset']}")

	@staticmethod
	def set_terminal_color(color: str):
		print(colors[color])