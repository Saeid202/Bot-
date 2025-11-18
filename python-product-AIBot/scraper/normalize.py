def normalize_product(raw):

	# takes a raw product dictionary and returns a standardized version of it with three consistent keys: "title", "price", and "source"
	return {
	     "title": raw["title"],
	     "price": raw["price"],
	     "source": raw.get("source", "Alibaba")
	}