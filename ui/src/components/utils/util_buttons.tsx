import React, {useEffect, useState} from "react"

import {useHistory, useLocation} from "react-router-dom"

import {Nav} from "react-bootstrap"
import {FontAwesomeIcon} from "@fortawesome/react-fontawesome"
import {faChevronLeft, faSync, faTrash, faEdit, faSave, faTimes} from "@fortawesome/free-solid-svg-icons"

import "./util_buttons.scss"

interface ButtonProps {
    onButtonClick?: () => void
    isDisabled?: boolean
}

export function BackButton(props: ButtonProps) {
    const history = useHistory()
    const location = useLocation()

    const [isPrevious, setIsPrevious] = useState(false)
    const [text, setText] = useState('')

    useEffect(() => {
        setText('Home')

        let previous_path = location.state
        if (previous_path) {
            if (previous_path === '/run') {
                setText('Run')
            } else if (previous_path === '/computer') {
                setText('Computer')
            }

            if (previous_path !== '/login') {
                setIsPrevious(true)
            }
        }

    }, [location])


    function onBackButtonClick() {
        if (props.onButtonClick) {
            props.onButtonClick()
        }

        if (isPrevious) {
            history.goBack()
        } else {
            let uri = location.pathname + location.search
            history.push('/home', uri)
        }
    }

    return <Nav.Link className={'tab'} onClick={onBackButtonClick}>
        <FontAwesomeIcon icon={faChevronLeft}/>
        <span>{text}</span>
    </Nav.Link>
}

export function RefreshButton(props: ButtonProps) {
    function onRefreshButtonClick() {
        if (props.onButtonClick) {
            props.onButtonClick()
        }
    }

    return <Nav.Link className={'tab float-right'} onClick={onRefreshButtonClick}>
        <FontAwesomeIcon icon={faSync}/>
    </Nav.Link>
}

export function DeleteButton(props: ButtonProps) {
    return <Nav.Link className={'tab float-right'} onClick={props.onButtonClick}>
        <FontAwesomeIcon icon={faTrash}/>
    </Nav.Link>
}

export function EditButton(props: ButtonProps) {
    return <Nav.Link className={'tab float-right'} onClick={props.onButtonClick}>
        <FontAwesomeIcon icon={faEdit}/>
    </Nav.Link>
}

export function SaveButton(props: ButtonProps) {
    return <Nav.Link onClick={props.onButtonClick} className={'tab float-right'} disabled={props.isDisabled}>
        <FontAwesomeIcon icon={faSave}/>
    </Nav.Link>
}

export function CancelButton(props: ButtonProps) {
    return <Nav.Link onClick={props.onButtonClick} className={'tab float-right'} disabled={props.isDisabled}>
        <FontAwesomeIcon icon={faTimes}/>
    </Nav.Link>
}