import './FilterSection.css'
import {Badge, Card} from 'react-bootstrap'
import {Link} from 'react-router-dom'
import {useQueryParams} from '../hooks/useQueryParams.ts'
import {X} from 'react-bootstrap-icons'

export const FilterSection = ({languages}: { languages: string[] }) => {
  const {language} = useQueryParams()

  return (
    <Card className='mx-auto mb-3 w-75'>
      <Card.Header>Filtering</Card.Header>
      <Card.Body>
        <Card.Title>Language</Card.Title>
        <div className='d-flex flex-wrap gap-2 py-2'>
          {languages.map(lang => (
            <FilterChip key={lang} current={lang} selected={language}/>
          ))}
        </div>
      </Card.Body>
    </Card>
  )
}

const FilterChip = ({current, selected}: { current: string, selected: string | null }) => {
  if (current === selected) {
    return (
      <Link key={current} to={({search: ''})}>
        <Badge pill bg='filter-active'>
          <div className='px-2'>{current}</div>
          <X size='20px' className='mr-1'/>
        </Badge>
      </Link>
    )
  } else {
    return (
      <Link key={current} to={({search: new URLSearchParams({language: current}).toString()})}>
        <Badge pill bg='filter'>
          <div className='px-2'>{current}</div>
        </Badge>
      </Link>
    )
  }
}