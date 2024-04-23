def draw_wrapped_string(string, x, y):
	width = 30
	lines = string.split('\n')
	
	cur_y = y
	linesize = 18
	num_lines = 0


	for line in lines:

		words = line.split(' ')
		words.reverse()
		cur_line = ""

		while words:
			future_line = cur_line + ' ' + words[-1] if cur_line else words[-1]

			if len(future_line) < width:
				cur_line = future_line
				words.pop()
			else:
				# Start a new line
				#self.draw_string(cur_line, surface, get_x(cur_line), cur_y, color)
				cur_y += linesize
				cur_line = ""
				num_lines += 1

		if cur_line:
			#self.draw_string(cur_line, surface, get_x(cur_line), cur_y, color)
			num_lines += 1

		if not line:
			num_lines += 1
		cur_y += linesize

	print(num_lines)

draw_wrapped_string("Hello\n\n there", 0, 0)