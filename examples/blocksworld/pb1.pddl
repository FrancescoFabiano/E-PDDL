(define (problem pb1)
  (:domain blocksworld)
  (:objects a b)
  (:agents ag1 ag2)
  (:init (onTable a) (onTable b) (clear a) (clear b) (equal a a) (equal b b) ([ag1](clear a)))
  (:goal (and (on a b))))