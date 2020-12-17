import React, {useEffect, useState} from "react"

import {Button, Form, Image} from "react-bootstrap"
import {useAuth0} from "@auth0/auth0-react"
import {captureException} from '@sentry/react'

import NETWORK from "../network"
import {LabLoader} from "../components/utils/loader"
import useWindowDimensions from "../utils/window_dimensions"
import {User} from "../models/user"
import CACHE from "../cache/cache"

import './settings_view.scss'
import HamburgerMenuBar from "../components/utils/hamburger_menu"

const DEFAULT_IMAGE = 'https://raw.githubusercontent.com/azouaoui-med/pro-sidebar-template/gh-pages/src/img/user.jpg'

function SettingsView() {
    let [user, setUser] = useState(null as unknown as User)
    const [isLoading, setIsLoading] = useState(true)

    const {logout} = useAuth0()

    const {width: windowWidth} = useWindowDimensions()
    const actualWidth = Math.min(800, windowWidth)

    useEffect(() => {
        const userCache = CACHE.getUser()

        async function load() {
            let currentUser = await userCache.get()
            if (currentUser) {
                setUser(currentUser)
                setIsLoading(false)
            }
        }

        load().then()
    }, [])

    function logOut() {
        NETWORK.signOut().then((res) => {
            if (res.is_successful) {
                logout({returnTo: window.location.origin})
            } else {
                captureException(Error('error in logout'))
            }
        })
    }

    return <div>
        <HamburgerMenuBar title={'Profile'}>
        </HamburgerMenuBar>
        {isLoading ?
            <LabLoader/>
            :
            <div className={'page pl-1 pr-1'} style={{width: actualWidth}}>
                <div className={'text-center'}>
                    <Image className={'image-style mt-2'}
                           src={user.picture ? user.picture : DEFAULT_IMAGE}
                           roundedCircle/>
                </div>
                <div className={'mt-5'}>
                    <Form>
                        <Form.Group controlId="token">
                            <Form.Label>Token</Form.Label>
                            <Form.Control type="text" value={`${user.default_project}`} disabled={true}/>
                        </Form.Group>
                        <Form.Group controlId="name">
                            <Form.Label>Name</Form.Label>
                            <Form.Control type="name" value={user.name} disabled={true}/>
                        </Form.Group>
                        <Form.Group controlId="email">
                            <Form.Label>Email</Form.Label>
                            <Form.Control type="email" value={user.email} disabled={true}/>
                        </Form.Group>
                    </Form>
                </div>
                <Button className={'mt-5'} onClick={logOut}>Log out</Button>
            </div>
        }
    </div>
}


export default SettingsView;