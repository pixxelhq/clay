package http

func (s *Server) MapRoutes() error {
	//middleware functions for all routes
	s.Router.Use(Logger())

	v1 := s.Router.Group("/v1/")
	{
		bh := NewBlock(s.Block)
		v1.POST("/blocks", bh.Create)
	}

	return nil
}
