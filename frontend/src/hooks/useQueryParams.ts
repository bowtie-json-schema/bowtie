import {useLocation} from 'react-router-dom'
import {useMemo} from 'react'

export const useQueryParams = () => {
  const { search } = useLocation();
  return useMemo(() => {
      const params = new URLSearchParams(search)
      return {
        language: params.get('language')
      }
    }, [search]);
}