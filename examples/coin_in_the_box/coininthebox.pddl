(define (domain coin_in_the_box)
  (:requirements :strips :negative-preconditions :no-duplicates :mep)
  (:predicates (opened) (has_key ?ag -agent) (looking ?ag - agent) (tail))
 

  (:action open
	:act_type 	ontic
    :parameters (?ag - agent)
    :precondition (and ([?ag](has_key ?ag1)) (has_key ?ag))
    :effect (opened)
	:observers (and (forall (?ag2 - agent) (when (looking ?ag2) (?ag2))) (?ag1))
  )

  (:action peek
	:act_type	sensing
    :parameters (?ag - agent)
    :precondition (and ([?ag](opened)) ([?ag](looking ?ag)) (looking ?ag) (opened))
    :effect (tail)
	:observers	(?ag)
	:p_observers (and (forall (?ag2 - agent) (when (?ag != ?ag2)((when (looking ?ag2) (?ag2))))))
	)
  

  (:action signal
    :parameters (?ag1 ?ag2 - agent)
    :precondition (and ([?ag1](looking ?ag1)) (looking ?ag1) (not ([?ag2](looking ?ag2))) (not (looking ?ag2)))
    :effect (looking ?ag2)
	:observers (?ag1 ?ag2)
  )

  (:action distract
    :parameters (?ag1 ?ag2 - agent)
    :precondition (and ([?ag1](looking ?ag1)) (looking ?ag1) ([?ag2](looking ?ag2)) (looking ?ag2))
    :effect (not (looking ?ag2))
	:observers (?ag1 ?ag2)
  )
  
  (:action shout
	:act_type	announcement
    :parameters (?ag - agent)
    :precondition (and ([?ag](tail)) (tail))
    :effect (tail)
	:observers (and (forall (?ag2 - agent) (when (?ag != ?ag2)((when (looking ?ag2) (?ag2))))) (?ag))
   )
	
)