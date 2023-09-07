package pkg

type StringSet struct {
	M map[string]struct{}
}

func (s *StringSet) AddItem(item string) {
	s.M[item] = struct{}{}
}

func (s *StringSet) HasItem(item string) bool {
	_, ok := s.M[item]
	return ok
}

func NewSet() *StringSet {
	s := &StringSet{}
	s.M = make(map[string]struct{})
	return s
}

func NewSetFromValues(items []string) *StringSet {
	s := NewSet()
	for _, i := range items {
		s.AddItem(i)
	}
	return s
}
